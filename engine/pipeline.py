import os
import sys
import time
import math
import argparse
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

from engine.gpx_parser import parse_gpx
from engine.media_processor import scan_media_folder, organize_windows_auto, prepare_cache_for_window
from engine.filmstrip_engine import render_filmstrip_frame, load_fonts as load_filmstrip_fonts, W_HALF, H, STRIDE, WIN_W, WIN_H, WIN_R_A, WIN_R_B, W_SUB
from engine.map_engine import compute_track_projection, create_base_canvas, render_map_frame
from engine.audio_mixer import mix_master_audio

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def run_pipeline(gpx_path, media_dir, output_path, bgm_choice='default', duration=None, fps=30, hud_title='CYCLING ROUTE RECAP', map_style='satellite', film_style='portra400'):
    t0 = time.time()
    print("=" * 60)
    print("🚴 Universal Cycling Route Video Generator")
    print("=" * 60)
    
    # 1. Parse GPX
    print(f"[*] Parsing GPX track from: {gpx_path}")
    gpx_data = parse_gpx(gpx_path)
    total_dist = gpx_data['total_distance_km']
    print(f"    - Total Distance: {total_dist} km")
    print(f"    - Total Climb: {gpx_data['total_climb_m']} m")
    print(f"    - Total Stages: {len(gpx_data['stages'])}")
    
    # 2. Scan & Organize Media
    print(f"[*] Scanning media folder: {media_dir}")
    media_files = scan_media_folder(media_dir)
    if not media_files:
        raise ValueError(f"No valid media files found in {media_dir}")
    print(f"    - Found {len(media_files)} media assets")
    
    windows = organize_windows_auto(media_files)
    num_windows = len(windows)
    print(f"    - Organized into {num_windows} filmstrip windows")
    
    # Cache setup
    tmp_dir = f"/tmp/cycling_video_{os.getpid()}"
    cache_dir = os.path.join(tmp_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    print("[*] Preparing frame caches...")
    for w_idx, win in enumerate(windows):
        prepare_cache_for_window(w_idx, win, cache_dir)
    print("    - All windows cached successfully!")
    
    # 3. Time & Physics calculations
    if duration is None:
        duration = max(30.0, num_windows * 2.2) # ~2.2s per window
    total_frames = int(duration * fps)
    
    y_total = max(0, (num_windows - 1) * STRIDE)
    v_actual = y_total / max(1.0, duration - 8.0) if duration > 8.0 else y_total / duration
    t_accel = 2.0
    t_decel = max(t_accel, duration - 3.0)
    
    def get_y_scroll(t):
        if t < t_accel:
            return 0.5 * (v_actual / t_accel) * t * t
        elif t <= t_decel:
            return 0.5 * v_actual * t_accel + v_actual * (t - t_accel)
        else:
            dt = t - t_decel
            decel = v_actual / max(0.1, duration - t_decel)
            return 0.5 * v_actual * t_accel + v_actual * (t_decel - t_accel) + v_actual * dt - 0.5 * decel * dt * dt

    # Preload frame file lists
    window_frames = []
    for w_idx, win in enumerate(windows):
        sub_lists = []
        for sub_idx in range(len(win['items'])):
            sdir = os.path.join(cache_dir, f'win_{w_idx:02d}_sub_{sub_idx}')
            flist = sorted([os.path.join(sdir, f) for f in os.listdir(sdir) if f.endswith('.jpg')])
            sub_lists.append(flist)
        window_frames.append(sub_lists)
        
    mask_a = Image.new('L', (WIN_W, WIN_H), 0)
    ImageDraw.Draw(mask_a).rounded_rectangle((0, 0, WIN_W, WIN_H), radius=WIN_R_A, fill=255)
    mask_b = Image.new('L', (W_SUB, WIN_H), 0)
    ImageDraw.Draw(mask_b).rounded_rectangle((0, 0, W_SUB, WIN_H), radius=WIN_R_B, fill=255)
    film_fonts = load_filmstrip_fonts()
    
    # 4. Map Setup
    projected_pts = compute_track_projection(gpx_data['points'])
    base_map_img = create_base_canvas(projected_pts)
    
    try:
        f_hud_title = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 13, index=1)
        f_hud_sub = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 13, index=2)
        f_hud_lbl = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 13, index=0)
        f_hud_val = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 15, index=1)
        f_trophy_title = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 21, index=2)
        f_trophy_sub = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 13, index=2)
    except Exception:
        f_hud_title = f_hud_sub = f_hud_lbl = f_hud_val = f_trophy_title = f_trophy_sub = ImageFont.load_default()
    map_fonts = (f_hud_title, f_hud_sub, f_hud_lbl, f_hud_val, f_trophy_title, f_trophy_sub)
    
    # 5. Render Left Map Video
    left_vid_path = os.path.join(tmp_dir, 'left_map.mp4')
    print(f"[*] Rendering Left Map Video ({total_frames} frames)...")
    cmd_left = [
        FFMPEG, '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{W_HALF}x{H}', '-pix_fmt', 'rgb24', '-r', str(fps),
        '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
        '-pix_fmt', 'yuv420p', left_vid_path
    ]
    proc_left = subprocess.Popen(cmd_left, stdin=subprocess.PIPE)
    for f_idx in range(total_frames):
        t = f_idx / float(fps)
        progress = min(1.0, t / duration)
        stage_idx = min(len(gpx_data['stages']) - 1, int(progress * len(gpx_data['stages'])))
        stage_info = gpx_data['stages'][stage_idx]
        frame_im = render_map_frame(base_map_img, projected_pts, progress, f_idx, stage_info, gpx_data, map_fonts, hud_title=hud_title)
        proc_left.stdin.write(frame_im.tobytes())
    proc_left.stdin.close()
    proc_left.wait()
    
    # 6. Render Right Filmstrip Video
    right_vid_path = os.path.join(tmp_dir, 'right_filmstrip.mp4')
    print(f"[*] Rendering Right Filmstrip Video ({total_frames} frames)...")
    cmd_right = [
        FFMPEG, '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{W_HALF}x{H}', '-pix_fmt', 'rgb24', '-r', str(fps),
        '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
        '-pix_fmt', 'yuv420p', right_vid_path
    ]
    proc_right = subprocess.Popen(cmd_right, stdin=subprocess.PIPE)
    for f_idx in range(total_frames):
        t = f_idx / float(fps)
        y_scroll = get_y_scroll(t)
        frame_im = render_filmstrip_frame(t, y_scroll, windows, window_frames, fps, v_actual, (mask_a, mask_b), film_fonts, film_style=film_style)
        proc_right.stdin.write(frame_im.tobytes())
    proc_right.stdin.close()
    proc_right.wait()
    
    # 7. Mix Master Audio
    bgm_map = {
        'default': '/Users/thhe2/agy/cycling-route-video/resources/bgm/bgm_acoustic_highway.m4a',
        'coastal': '/Users/thhe2/agy/cycling-route-video/resources/bgm/bgm_coastal_beat.m4a',
        'epic': '/Users/thhe2/agy/cycling-route-video/resources/bgm/bgm_epic_mountain.m4a'
    }
    bgm_file = bgm_map.get(bgm_choice, bgm_choice)
    audio_path = os.path.join(tmp_dir, 'master_audio.m4a')
    print(f"[*] Mixing Master Audio from: {os.path.basename(bgm_file)}")
    mix_master_audio(bgm_file, duration, audio_path)
    
    # 8. Assemble Master Video (1920x1080)
    print(f"[*] Compositing Master 1080p Video -> {output_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd_master = [
        FFMPEG, '-y',
        '-i', left_vid_path,
        '-i', right_vid_path,
        '-i', audio_path,
        '-filter_complex', '[0:v][1:v]hstack=inputs=2[vout]',
        '-map', '[vout]',
        '-map', '2:a',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '256k',
        output_path
    ]
    subprocess.run(cmd_master, check=True)
    
    # Cleanup temp directory
    shutil.rmtree(tmp_dir, ignore_errors=True)
    
    print("=" * 60)
    print(f"🎉 Master Video Successfully Rendered in {time.time() - t0:.1f}s!")
    print(f"📍 Output: {output_path} ({os.path.getsize(output_path)/(1024*1024):.1f} MB)")
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Universal Cycling Route Video Generator")
    parser.add_argument('--gpx', required=True, help="Path to GPX track file")
    parser.add_argument('--media', required=True, help="Path to folder containing photos/videos")
    parser.add_argument('--output', default="recap_video.mp4", help="Output MP4 file path")
    parser.add_argument('--bgm', default="default", help="BGM choice (default, coastal, epic or custom file path)")
    parser.add_argument('--duration', type=float, default=None, help="Video duration in seconds")
    parser.add_argument('--hud-title', default="CYCLING ROUTE RECAP", help="Custom HUD title text")
    parser.add_argument('--map-style', default="satellite", choices=['satellite', 'dark', 'topo', 'light'], help="Map underlay style")
    parser.add_argument('--film-style', default="portra400", choices=['portra400', 'gold200', 'fuji400', 'ilford400'], help="35mm Film stock theme")
    
    args = parser.parse_args()
    run_pipeline(
        args.gpx, args.media, args.output, args.bgm, args.duration,
        hud_title=args.hud_title, map_style=args.map_style, film_style=args.film_style
    )
