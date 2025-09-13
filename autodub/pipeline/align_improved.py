import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from pydub import AudioSegment
from ..config import TEMP_DIR

class ImprovedAligner:
    """
    Improved audio alignment with gentler speed adjustments and smart timing.
    """
    
    # Speed adjustment parameters
    MAX_SPEED_FACTOR = 1.4  # Max 40% faster (was 2.0x)
    MIN_SPEED_FACTOR = 0.7  # Max 30% slower (was 0.5x)
    
    # Tolerance thresholds
    PERFECT_THRESHOLD = 0.05  # ±5% timing difference = no adjustment
    GENTLE_THRESHOLD = 0.15   # ±15% = gentle adjustment
    MODERATE_THRESHOLD = 0.30  # ±30% = moderate adjustment
    
    def __init__(self):
        self.segments_info = []
        
    def analyze_timing(self, segments: List[Dict]) -> List[Dict]:
        """
        Analyze timing requirements and plan adjustments.
        """
        timing_analysis = []
        
        for i, segment in enumerate(segments):
            if not (segment.get('audio_path') and segment['audio_path'].exists()):
                continue
                
            audio = AudioSegment.from_file(segment['audio_path'])
            
            start_ms = int(segment['start'] * 1000)
            end_ms = int(segment['end'] * 1000)
            target_duration_ms = end_ms - start_ms
            current_duration_ms = len(audio)
            
            # Calculate timing difference ratio
            duration_ratio = current_duration_ms / target_duration_ms
            
            # Determine silence windows (gaps before/after segment)
            prev_end = segments[i-1]['end'] * 1000 if i > 0 else 0
            next_start = segments[i+1]['start'] * 1000 if i < len(segments)-1 else float('inf')
            
            silence_before = start_ms - prev_end
            silence_after = next_start - end_ms
            
            timing_analysis.append({
                'index': i,
                'segment': segment,
                'audio': audio,
                'start_ms': start_ms,
                'end_ms': end_ms,
                'target_duration_ms': target_duration_ms,
                'current_duration_ms': current_duration_ms,
                'duration_ratio': duration_ratio,
                'silence_before': silence_before,
                'silence_after': silence_after,
                'adjustment_needed': abs(1.0 - duration_ratio) > self.PERFECT_THRESHOLD
            })
            
        return timing_analysis
    
    def calculate_gentle_speed(self, duration_ratio: float) -> float:
        """
        Calculate a gentle speed adjustment factor.
        Instead of exact matching, we aim for reasonable approximation.
        """
        adjust_factor = 1.0 / duration_ratio
        
        # Apply different strategies based on the ratio
        if abs(1.0 - duration_ratio) <= self.PERFECT_THRESHOLD:
            # Very close - no adjustment needed
            return 1.0
            
        elif abs(1.0 - duration_ratio) <= self.GENTLE_THRESHOLD:
            # Small difference - apply 50% of needed adjustment
            partial_adjust = 1.0 + (adjust_factor - 1.0) * 0.5
            return max(self.MIN_SPEED_FACTOR, min(self.MAX_SPEED_FACTOR, partial_adjust))
            
        elif abs(1.0 - duration_ratio) <= self.MODERATE_THRESHOLD:
            # Moderate difference - apply 70% of needed adjustment
            partial_adjust = 1.0 + (adjust_factor - 1.0) * 0.7
            return max(self.MIN_SPEED_FACTOR, min(self.MAX_SPEED_FACTOR, partial_adjust))
            
        else:
            # Large difference - cap at maximum allowed adjustment
            return max(self.MIN_SPEED_FACTOR, min(self.MAX_SPEED_FACTOR, adjust_factor))
    
    def adjust_audio_speed(self, input_path: Path, output_path: Path, speed_factor: float):
        """
        Adjust audio speed using ffmpeg with chain of atempo filters for larger adjustments.
        """
        if abs(speed_factor - 1.0) < 0.01:
            # No adjustment needed
            return AudioSegment.from_file(input_path)
        
        # FFmpeg atempo can only do 0.5x to 2.0x per filter
        # For larger adjustments, we need to chain multiple filters
        filters = []
        remaining_factor = speed_factor
        
        while remaining_factor < 0.5 or remaining_factor > 2.0:
            if remaining_factor < 0.5:
                filters.append("atempo=0.5")
                remaining_factor /= 0.5
            else:
                filters.append("atempo=2.0")
                remaining_factor /= 2.0
        
        if abs(remaining_factor - 1.0) > 0.01:
            filters.append(f"atempo={remaining_factor}")
        
        if not filters:
            return AudioSegment.from_file(input_path)
        
        filter_chain = ",".join(filters)
        
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-filter:a', filter_chain,
            '-y', str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            return AudioSegment.from_file(output_path)
        else:
            # Fallback to original if adjustment fails
            print(f"Warning: Speed adjustment failed for factor {speed_factor:.2f}")
            return AudioSegment.from_file(input_path)
    
    def apply_smart_alignment(self, timing_analysis: List[Dict]) -> AudioSegment:
        """
        Apply smart alignment with borrowing from silence periods.
        """
        combined = AudioSegment.silent(duration=0)
        last_position_ms = 0
        
        for i, info in enumerate(timing_analysis):
            segment = info['segment']
            audio = info['audio']
            
            # Add silence before segment if needed
            if info['start_ms'] > last_position_ms:
                silence_duration = info['start_ms'] - last_position_ms
                combined += AudioSegment.silent(duration=silence_duration)
            
            if not info['adjustment_needed']:
                # No adjustment needed - use original audio
                combined += audio
                last_position_ms = info['start_ms'] + len(audio)
                
            else:
                # Calculate gentle speed adjustment
                speed_factor = self.calculate_gentle_speed(info['duration_ratio'])
                
                if speed_factor != 1.0:
                    # Apply speed adjustment
                    adjusted_path = TEMP_DIR / f"adjusted_{i:04d}.mp3"
                    adjusted_audio = self.adjust_audio_speed(
                        segment['audio_path'], 
                        adjusted_path, 
                        speed_factor
                    )
                    
                    # Check if we can borrow time from surrounding silences
                    new_duration = len(adjusted_audio)
                    overhang = new_duration - info['target_duration_ms']
                    
                    if overhang > 0:
                        # Audio is still too long after adjustment
                        # Try to borrow from surrounding silence
                        can_borrow_before = min(overhang / 2, info['silence_before'] * 0.5)
                        can_borrow_after = min(overhang / 2, info['silence_after'] * 0.5)
                        
                        if can_borrow_before + can_borrow_after >= overhang * 0.8:
                            # We can accommodate most of the overhang
                            # Shift the segment timing slightly
                            print(f"Segment {i}: Borrowing {can_borrow_before:.0f}ms before, {can_borrow_after:.0f}ms after")
                            # Reduce the silence we added before
                            if can_borrow_before > 0 and len(combined) > can_borrow_before:
                                # Remove some silence from before
                                combined = combined[:-int(can_borrow_before)]
                            combined += adjusted_audio
                        else:
                            # Can't borrow enough - use adjusted audio with slight trimming
                            combined += adjusted_audio[:info['target_duration_ms']]
                    else:
                        combined += adjusted_audio
                    
                    print(f"Segment {i}: Applied speed factor {speed_factor:.2f} (ratio was {info['duration_ratio']:.2f})")
                    last_position_ms = info['start_ms'] + len(adjusted_audio)
                    
                else:
                    # Speed adjustment would be negligible
                    combined += audio
                    last_position_ms = info['start_ms'] + len(audio)
        
        return combined
    
    def align_segments(self, segments: List[Dict]) -> Path:
        """
        Main alignment function with improved algorithm.
        """
        print("Analyzing timing requirements...")
        timing_analysis = self.analyze_timing(segments)
        
        print(f"Applying smart alignment to {len(timing_analysis)} segments...")
        combined = self.apply_smart_alignment(timing_analysis)
        
        output_path = TEMP_DIR / "dubbed_audio.wav"
        combined.export(output_path, format="wav")
        print(f"Aligned audio saved to: {output_path}")
        
        return output_path

# Backward compatibility wrapper
def align_segments(segments: List[Dict]) -> Path:
    """
    Align synthesized audio segments to original timing using improved algorithm.
    """
    aligner = ImprovedAligner()
    return aligner.align_segments(segments)