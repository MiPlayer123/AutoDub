import subprocess
from pathlib import Path
from ..config import TEMP_DIR

def mix_audio_simple(dubbed_vocals_path: Path, background_path: Path) -> Path:
    """
    Simple mixing of dubbed vocals with background using FFmpeg.
    
    Args:
        dubbed_vocals_path: Path to dubbed vocals
        background_path: Path to background audio
        
    Returns:
        Path to mixed audio file
    """
    print("Mixing dubbed vocals with background...")
    
    mixed_path = TEMP_DIR / "mixed_final.wav"
    
    # Use FFmpeg to mix the two audio tracks
    cmd = [
        'ffmpeg',
        '-i', str(dubbed_vocals_path),
        '-i', str(background_path),
        '-filter_complex',
        '[0:a]volume=1.0[vocals];[1:a]volume=0.7[bg];[vocals][bg]amix=inputs=2:duration=longest',
        '-ar', '44100',
        '-ac', '2',
        '-y', str(mixed_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Mixing failed, using dubbed vocals only: {result.stderr}")
        return dubbed_vocals_path
    
    print(f"Mixed audio saved to: {mixed_path}")
    return mixed_path