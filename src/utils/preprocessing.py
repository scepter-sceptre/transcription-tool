import subprocess
from pathlib import Path
import tempfile
from typing import Optional

def extract_audio_if_video(input_path: str) -> tuple[str, Optional[str]]:
    path = Path(input_path)
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    
    if path.suffix.lower() not in video_extensions:
        return input_path, None
    
    temp_audio = Path(tempfile.gettempdir()) / f"{path.stem}_audio.wav"
    
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-y',
        str(temp_audio)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return str(temp_audio), str(temp_audio)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to extract audio: {e.stderr.decode()}")