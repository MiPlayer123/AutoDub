import subprocess
import os
from pathlib import Path
from typing import Tuple
import yt_dlp
from ..config import TEMP_DIR

def download_video(url: str, output_name: str = "input") -> Tuple[Path, Path]:
    """
    Download video from YouTube and extract audio.
    Returns paths to video and audio files.
    """
    video_path = TEMP_DIR / f"{output_name}.mp4"
    audio_path = TEMP_DIR / f"{output_name}.wav"
    
    print(f"Downloading video from: {url}")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': str(video_path),
        'quiet': False,
        'no_warnings': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"Downloaded: {info.get('title', 'Unknown')}")
    
    print("Extracting audio...")
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-vn', '-ar', '44100', '-ac', '2',
        '-f', 'wav', str(audio_path),
        '-y'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    print(f"Audio extracted to: {audio_path}")
    return video_path, audio_path