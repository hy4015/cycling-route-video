import os
import subprocess
from PIL import Image, ImageOps
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def scan_media_folder(media_dir):
    """
    Scans media folder, sorts items, detects orientation and returns structured items.
    """
    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.mov', '.mp4'}
    files = []
    for f in sorted(os.listdir(media_dir)):
        ext = os.path.splitext(f)[1].lower()
        if ext in valid_exts and not f.startswith('.'):
            files.append(os.path.join(media_dir, f))
    return files

def get_image_aspect_ratio(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.heic':
        tmp_jpg = f'/tmp/probe_{os.getpid()}.jpg'
        try:
            subprocess.run(['sips', '-s', 'format', 'jpeg', file_path, '--out', tmp_jpg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            im = Image.open(tmp_jpg)
            im = ImageOps.exif_transpose(im)
            w, h = im.size
            if os.path.exists(tmp_jpg):
                os.remove(tmp_jpg)
            return w / float(h)
        except Exception:
            return 1.0
    elif ext in {'.jpg', '.jpeg', '.png'}:
        try:
            im = Image.open(file_path)
            im = ImageOps.exif_transpose(im)
            w, h = im.size
            return w / float(h)
        except Exception:
            return 1.0
    else:
        # Video
        return 1.77 # Default landscape video

def organize_windows_auto(media_files):
    """
    Auto-organizes media files into windows:
    - Vertical items (aspect < 1.0) paired into Type 'B' (Dual Magazine 428x484)
    - Horizontal items (aspect >= 1.0) framed into Type 'A' (Single Full Bleed 872x484)
    """
    windows = []
    i = 0
    n = len(media_files)
    while i < n:
        curr = media_files[i]
        ar_curr = get_image_aspect_ratio(curr)
        
        # If portrait, check if next is also portrait for dual pairing
        if ar_curr < 1.0 and i + 1 < n:
            next_f = media_files[i + 1]
            ar_next = get_image_aspect_ratio(next_f)
            if ar_next < 1.0:
                windows.append({'type': 'B', 'items': [curr, next_f]})
                i += 2
                continue
                
        # Otherwise single window
        windows.append({'type': 'A', 'items': [curr]})
        i += 1
        
    return windows

def prepare_cache_for_window(win_idx, win, cache_dir):
    """
    Prepares scaled frames for window win_idx into cache_dir.
    """
    w_type = win['type']
    target_w = 872 if w_type == 'A' else 428
    target_h = 484
    
    for sub_idx, file_path in enumerate(win['items']):
        sub_dir = os.path.join(cache_dir, f'win_{win_idx:02d}_sub_{sub_idx}')
        os.makedirs(sub_dir, exist_ok=True)
        
        existing = [f for f in os.listdir(sub_dir) if f.endswith('.jpg')]
        if existing:
            continue
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.heic'}:
            tmp_jpg = f'/tmp/conv_{win_idx}_{sub_idx}_{os.getpid()}.jpg'
            if ext == '.heic':
                subprocess.run(['sips', '-s', 'format', 'jpeg', file_path, '--out', tmp_jpg],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                im = Image.open(tmp_jpg)
            else:
                im = Image.open(file_path)
                
            im = ImageOps.exif_transpose(im)
            # Center crop with safe headroom (0.5, 0.1)
            im_fitted = ImageOps.fit(im, (target_w, target_h), centering=(0.5, 0.1), method=Image.Resampling.LANCZOS)
            im_fitted.convert('RGB').save(os.path.join(sub_dir, 'frame_0000.jpg'), quality=95)
            if os.path.exists(tmp_jpg):
                os.remove(tmp_jpg)
        else:
            # Video: extract up to 5s at 30fps
            cmd = [
                FFMPEG, '-y', '-i', file_path,
                '-t', '5.0',
                '-vf', f'scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}',
                '-r', '30',
                os.path.join(sub_dir, 'frame_%04d.jpg')
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
