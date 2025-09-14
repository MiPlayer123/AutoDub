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
                    
                else:  # Any amount of speedup needed - NO LIMITS!
                    # Apply speed adjustment with no cap as requested
                    atempo_factor = speed_needed  # FIXED: atempo > 1.0 speeds up
                    
                    temp_path = TEMP_DIR / f"adjusted_{i:04d}.wav"
                    adjust_audio_simple(segment['audio_path'], temp_path, atempo_factor)
                    adjusted_audio = AudioSegment.from_file(temp_path)
                    
                    combined = combined.overlay(adjusted_audio, position=start_ms)
                    placed_count += 1
                    adjusted_count += 1
                    
                    print(f"  Segment {i}: Compressed {speed_needed:.1f}x to fit")
                    temp_path.unlink()
                
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
    Adjust audio speed using ffmpeg atempo filter with NO SPEED LIMITS.
    atempo_factor: > 1.0 speeds up (shortens), < 1.0 slows down (lengthens)
    Chains multiple atempo filters to achieve any speed.
    """
    # Build atempo chain for any speed - NO LIMITS!
    if atempo_factor <= 0.5:
        # Very slow - chain multiple atempo filters
        filters = []
        remaining = atempo_factor
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining *= 2
        if remaining < 1.0:
            filters.append(f"atempo={remaining}")
        filter_chain = ','.join(filters)
    elif atempo_factor >= 2.0:
        # Fast speedup - chain multiple atempo filters  
        filters = []
        remaining = atempo_factor
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        if remaining > 1.0:
            filters.append(f"atempo={remaining}")
        filter_chain = ','.join(filters)
    else:
        # Single atempo is enough (0.5 <= factor <= 2.0)
        filter_chain = f'atempo={atempo_factor}'
    
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-filter:a', filter_chain,
        '-y', str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)