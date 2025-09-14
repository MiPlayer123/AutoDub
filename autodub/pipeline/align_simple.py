import subprocess
from pathlib import Path
from typing import List, Dict
from pydub import AudioSegment
from ..config import TEMP_DIR

def align_segments_simple(segments: List[Dict]) -> Path:
    """
    Simple, reliable alignment that preserves timing without overlaps.
    """
    print("Aligning audio segments (simple method)...")
    
    if not segments:
        raise ValueError("No segments to align")
    
    # Get total duration from last segment
    total_duration_ms = int(segments[-1]['end'] * 1000)
    
    # Create base silent track
    combined = AudioSegment.silent(duration=total_duration_ms)
    
    placed_count = 0
    adjusted_count = 0
    
    for i, segment in enumerate(segments):
        if not segment.get('audio_path') or not segment['audio_path'].exists():
            continue
        
        try:
            # Load synthesized audio
            audio = AudioSegment.from_file(segment['audio_path'])
            
            # Calculate timing
            start_ms = int(segment['start'] * 1000)
            end_ms = int(segment['end'] * 1000)
            target_duration_ms = end_ms - start_ms
            current_duration_ms = len(audio)
            
            # Calculate how much we need to adjust
            if current_duration_ms > 0:
                # CORRECT calculation: if audio is longer, we need to speed it up (factor > 1)
                speed_needed = current_duration_ms / target_duration_ms
                
                # Decide what to do based on speed needed
                if speed_needed <= 1.15:  # Audio fits or needs minor speedup
                    # Place as-is or with minor adjustment
                    if speed_needed > 1.0:
                        # Need to speed up audio (make it shorter)
                        # For ffmpeg atempo: >1.0 speeds up, <1.0 slows down
                        atempo_factor = speed_needed  # This actually speeds it up!
                        
                        temp_path = TEMP_DIR / f"adjusted_{i:04d}.wav"
                        adjust_audio_simple(segment['audio_path'], temp_path, atempo_factor)
                        adjusted_audio = AudioSegment.from_file(temp_path)
                        
                        # Verify it worked
                        new_duration = len(adjusted_audio)
                        
                        combined = combined.overlay(adjusted_audio, position=start_ms)
                        adjusted_count += 1
                        temp_path.unlink()
                    else:
                        # Audio is shorter than target, place as-is
                        combined = combined.overlay(audio, position=start_ms)
                    
                    placed_count += 1
                    
                elif speed_needed <= 2.0:  # Moderate speedup needed (increased threshold)
                    # Apply more aggressive speed adjustment
                    atempo_factor = speed_needed  # FIXED: atempo > 1.0 speeds up
                    
                    temp_path = TEMP_DIR / f"adjusted_{i:04d}.wav"
                    adjust_audio_simple(segment['audio_path'], temp_path, atempo_factor)
                    adjusted_audio = AudioSegment.from_file(temp_path)
                    
                    combined = combined.overlay(adjusted_audio, position=start_ms)
                    placed_count += 1
                    adjusted_count += 1
                    
                    print(f"  Segment {i}: Compressed {speed_needed:.1f}x to fit")
                    temp_path.unlink()
                    
                else:  # Too much speedup needed
                    # Truncate to fit
                    truncated_audio = audio[:target_duration_ms]
                    combined = combined.overlay(truncated_audio, position=start_ms)
                    placed_count += 1
                    print(f"  Segment {i}: Truncated (was {speed_needed:.1f}x too long)")
                
        except Exception as e:
            print(f"  Failed to place segment {i}: {e}")
    
    # Save the result
    output_path = TEMP_DIR / "dubbed_audio.wav"
    combined.export(output_path, format="wav")
    
    print(f"Alignment completed:")
    print(f"  ✅ Placed: {placed_count} segments")
    print(f"  🎛️ Adjusted: {adjusted_count} segments")
    print(f"  📁 Output: {output_path}")
    
    return output_path

def adjust_audio_simple(input_path: Path, output_path: Path, atempo_factor: float):
    """
    Adjust audio speed using ffmpeg atempo filter.
    atempo_factor: > 1.0 speeds up (shortens), < 1.0 slows down (lengthens)
    """
    # Clamp to ffmpeg atempo limits
    atempo_factor = max(0.5, min(2.0, atempo_factor))
    
    # If factor is outside single atempo range, chain filters
    if atempo_factor < 0.5:
        # Need double speedup
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-filter:a', 'atempo=0.5,atempo=0.8',
            '-y', str(output_path)
        ]
    elif atempo_factor > 2.0:
        # Need double slowdown  
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-filter:a', 'atempo=2.0,atempo=1.5',
            '-y', str(output_path)
        ]
    else:
        # Single atempo is enough
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-filter:a', f'atempo={atempo_factor}',
            '-y', str(output_path)
        ]
    
    subprocess.run(cmd, capture_output=True, check=True)