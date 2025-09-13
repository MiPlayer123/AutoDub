import subprocess
from pathlib import Path
from typing import List, Dict
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from ..config import TEMP_DIR

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds."""
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0

def adjust_audio_speed(input_path: Path, output_path: Path, speed_factor: float):
    """Adjust audio speed using ffmpeg atempo filter."""
    if speed_factor < 0.5:
        speed_factor = 0.5
    elif speed_factor > 2.0:
        speed_factor = 2.0
    
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-filter:a', f'atempo={speed_factor}',
        '-y', str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)

def align_segments(segments: List[Dict]) -> Path:
    """
    Align synthesized audio segments to original timing.
    Creates a single continuous audio track.
    """
    print("Aligning audio segments...")
    
    combined = AudioSegment.silent(duration=0)
    last_end_time = 0
    
    for i, segment in enumerate(segments):
        if segment.get('audio_path') and segment['audio_path'].exists():
            audio = AudioSegment.from_file(segment['audio_path'])
            
            start_ms = int(segment['start'] * 1000)
            end_ms = int(segment['end'] * 1000)
            target_duration_ms = end_ms - start_ms
            current_duration_ms = len(audio)
            
            if start_ms > last_end_time:
                silence_duration = start_ms - last_end_time
                combined += AudioSegment.silent(duration=silence_duration)
            
            speed_factor = current_duration_ms / target_duration_ms
            
            if 0.8 <= speed_factor <= 1.2:
                combined += audio
            else:
                adjusted_path = TEMP_DIR / f"adjusted_{i:04d}.mp3"
                adjust_speed_factor = 1.0 / speed_factor
                
                if 0.5 <= adjust_speed_factor <= 2.0:
                    try:
                        adjust_audio_speed(segment['audio_path'], adjusted_path, adjust_speed_factor)
                        adjusted_audio = AudioSegment.from_file(adjusted_path)
                        combined += adjusted_audio
                        print(f"Adjusted speed of segment {i} by factor {adjust_speed_factor:.2f}")
                    except:
                        combined += audio[:target_duration_ms] if len(audio) > target_duration_ms else audio
                else:
                    if len(audio) > target_duration_ms:
                        combined += audio[:target_duration_ms]
                    else:
                        combined += audio
                        padding = target_duration_ms - len(audio)
                        if padding > 0:
                            combined += AudioSegment.silent(duration=padding)
            
            last_end_time = start_ms + len(combined[start_ms:])
    
    output_path = TEMP_DIR / "dubbed_audio.wav"
    combined.export(output_path, format="wav")
    print(f"Aligned audio saved to: {output_path}")
    
    return output_path