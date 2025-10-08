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
        'format': 'best[height<=1080]/best',
        'outtmpl': str(video_path),
        'quiet': False,
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['js', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"Downloaded: {info.get('title', 'Unknown')}")
    except Exception as e:
        print(f"Download failed: {e}")
        print("Trying alternative format selection...")
        # Fallback with more permissive format selection
        fallback_opts = {
            'format': 'best',
            'outtmpl': str(video_path),
            'quiet': False,
            'no_warnings': False,
        }
        try:
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                print(f"Downloaded (fallback): {info.get('title', 'Unknown')}")
        except Exception as e2:
            print(f"Fallback download also failed: {e2}")
            raise Exception(f"Failed to download video from {url}. The video may be private, age-restricted, or region-locked. Error: {e}")
    
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