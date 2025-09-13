import subprocess
from pathlib import Path
from ..config import OUTPUT_DIR

def mux_video(video_path: Path, audio_path: Path, output_name: str = "output") -> Path:
    """
    Combine video with new dubbed audio track.
    """
    output_path = OUTPUT_DIR / f"{output_name}_dubbed.mp4"
    
    print(f"Muxing video and audio...")
    print(f"  Video: {video_path}")
    print(f"  Audio: {audio_path}")
    print(f"  Output: {output_path}")
    
    cmd = [
        'ffmpeg', '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '192k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-y', str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg muxing error: {result.stderr}")
    
    print(f"Successfully created dubbed video: {output_path}")
    return output_path