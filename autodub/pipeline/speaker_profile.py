import librosa
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess
import tempfile

def extract_speaker_audio(segments: List[Dict], vocals_path: Path, speaker_id: int) -> Path:
    """
    Extract audio segments for a specific speaker and concatenate them.
    """
    temp_files = []
    
    try:
        # Create temporary files for each segment of this speaker
        for i, segment in enumerate(segments):
            if segment['speaker'] == speaker_id:
                temp_file = Path(tempfile.mktemp(suffix='.wav'))
                temp_files.append(temp_file)
                
                # Extract this segment using ffmpeg
                subprocess.run([
                    'ffmpeg', '-i', str(vocals_path),
                    '-ss', str(segment['start']),
                    '-t', str(segment['end'] - segment['start']),
                    '-ar', '22050', '-ac', '1',  # Mono, 22050 Hz for analysis
                    '-y', str(temp_file)
                ], capture_output=True, check=True)
        
        if not temp_files:
            raise ValueError(f"No segments found for speaker {speaker_id}")
        
        # Concatenate all segments for this speaker
        speaker_audio_path = Path(tempfile.mktemp(suffix=f'_speaker_{speaker_id}.wav'))
        
        if len(temp_files) == 1:
            # If only one segment, just copy it
            subprocess.run(['cp', str(temp_files[0]), str(speaker_audio_path)], check=True)
        else:
            # Concatenate multiple segments
            input_list = '|'.join(str(f) for f in temp_files)
            subprocess.run([
                'ffmpeg', '-i', f'concat:{input_list}',
                '-acodec', 'copy', '-y', str(speaker_audio_path)
            ], capture_output=True, check=True)
        
        return speaker_audio_path
        
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()

def analyze_speaker_characteristics(audio_path: Path) -> Dict:
    """
    Analyze vocal characteristics of a speaker's audio.
    Returns characteristics that can be used for voice matching.
    """
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=22050)
        
        if len(y) < sr * 0.5:  # Less than 0.5 seconds
            print(f"Warning: Very short audio sample for analysis ({len(y)/sr:.2f}s)")
        
        # Extract features
        characteristics = {}
        
        # Fundamental frequency (pitch)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if pitch_values:
            characteristics['mean_pitch'] = np.mean(pitch_values)
            characteristics['pitch_std'] = np.std(pitch_values)
            characteristics['pitch_range'] = np.max(pitch_values) - np.min(pitch_values)
        else:
            characteristics['mean_pitch'] = 150.0  # Default fallback
            characteristics['pitch_std'] = 20.0
            characteristics['pitch_range'] = 50.0
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        characteristics['spectral_centroid'] = np.mean(spectral_centroids)
        
        # Zero crossing rate (roughness indicator)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        characteristics['zero_crossing_rate'] = np.mean(zcr)
        
        # Energy/loudness
        rms = librosa.feature.rms(y=y)[0]
        characteristics['rms_energy'] = np.mean(rms)
        
        # Estimate gender based on pitch
        mean_pitch = characteristics['mean_pitch']
        if mean_pitch < 165:  # Typical male range
            characteristics['estimated_gender'] = 'male'
            characteristics['gender_confidence'] = min(0.9, (165 - mean_pitch) / 50)
        elif mean_pitch > 200:  # Typical female range  
            characteristics['estimated_gender'] = 'female'
            characteristics['gender_confidence'] = min(0.9, (mean_pitch - 200) / 50)
        else:  # Ambiguous range
            characteristics['estimated_gender'] = 'neutral'
            characteristics['gender_confidence'] = 0.5
        
        return characteristics
        
    except Exception as e:
        print(f"Error analyzing speaker characteristics: {e}")
        # Return default characteristics
        return {
            'mean_pitch': 150.0,
            'pitch_std': 20.0,
            'pitch_range': 50.0,
            'spectral_centroid': 2000.0,
            'zero_crossing_rate': 0.1,
            'rms_energy': 0.1,
            'estimated_gender': 'neutral',
            'gender_confidence': 0.5
        }

def build_speaker_profiles(segments: List[Dict], vocals_path: Path) -> Dict[int, Dict]:
    """
    Build vocal characteristic profiles for each speaker.
    
    Args:
        segments: List of transcribed segments with speaker IDs
        vocals_path: Path to separated vocals audio file
        
    Returns:
        Dictionary mapping speaker_id -> characteristics
    """
    print("Building speaker profiles...")
    
    # Get unique speakers
    speakers = set(segment['speaker'] for segment in segments)
    print(f"Found {len(speakers)} unique speakers: {sorted(speakers)}")
    
    profiles = {}
    
    for speaker_id in speakers:
        print(f"Analyzing speaker {speaker_id}...")
        
        try:
            # Extract audio for this speaker
            speaker_audio_path = extract_speaker_audio(segments, vocals_path, speaker_id)
            
            # Analyze characteristics
            characteristics = analyze_speaker_characteristics(speaker_audio_path)
            
            # Add segment count and total duration
            speaker_segments = [s for s in segments if s['speaker'] == speaker_id]
            characteristics['segment_count'] = len(speaker_segments)
            characteristics['total_duration'] = sum(s['end'] - s['start'] for s in speaker_segments)
            
            profiles[speaker_id] = characteristics
            
            print(f"Speaker {speaker_id}: {characteristics['estimated_gender']} "
                  f"({characteristics['mean_pitch']:.1f}Hz pitch, "
                  f"{characteristics['segment_count']} segments)")
            
            # Clean up temporary file
            if speaker_audio_path.exists():
                speaker_audio_path.unlink()
                
        except Exception as e:
            print(f"Failed to analyze speaker {speaker_id}: {e}")
            # Create minimal profile
            profiles[speaker_id] = {
                'mean_pitch': 150.0,
                'estimated_gender': 'neutral',
                'gender_confidence': 0.5,
                'segment_count': len([s for s in segments if s['speaker'] == speaker_id]),
                'total_duration': sum(s['end'] - s['start'] for s in segments if s['speaker'] == speaker_id)
            }
    
    return profiles