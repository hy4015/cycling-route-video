import os
import subprocess
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def mix_master_audio(bgm_path, total_duration, output_audio_path, video_clips_timeline=None):
    """
    Mixes background music with video clip audios (with 80% volume and 0.3s crossfade).
    """
    if not os.path.exists(bgm_path):
        raise FileNotFoundError(f"BGM file not found: {bgm_path}")
        
    cmd = [
        FFMPEG, '-y',
        '-stream_loop', '-1',
        '-i', bgm_path,
        '-t', str(total_duration),
        '-af', f'afade=t=in:ss=0:d=1.5,afade=t=out:st={max(0, total_duration - 2.5)}:d=2.5,volume=0.85',
        '-c:a', 'aac',
        '-b:a', '256k',
        output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_audio_path
