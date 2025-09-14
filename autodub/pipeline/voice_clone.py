import requests
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from ..config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL

def extract_speaker_audio_for_cloning(segments: List[Dict], audio_path: Path, speaker_id: int) -> Optional[Path]:
    """
    Extract audio samples for a specific speaker for voice cloning.
    Extracts up to 60 seconds of the cleanest audio.
    """
    
    speaker_segments = [s for s in segments if s['speaker'] == speaker_id]
    if not speaker_segments:
        return None
    
    # Sort by confidence and take best segments
    speaker_segments.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # Extract up to 60 seconds of audio
    total_duration = 0
    selected_segments = []
    
    for segment in speaker_segments:
        segment_duration = segment['end'] - segment['start']
        if total_duration + segment_duration <= 60:  # Max 60 seconds
            selected_segments.append(segment)
            total_duration += segment_duration
        
        if total_duration >= 30:  # We have enough
            break
    
    if total_duration < 10:  # Need at least 10 seconds
        print(f"  Not enough audio for Speaker {speaker_id} ({total_duration:.1f}s)")
        return None
    
    print(f"  Extracting {total_duration:.1f}s for Speaker {speaker_id}")
    
    # Create temporary files for segments
    temp_files = []
    try:
        for i, segment in enumerate(selected_segments):
            temp_file = Path(tempfile.mktemp(suffix=f'_speaker_{speaker_id}_{i}.wav'))
            temp_files.append(temp_file)
            
            # Extract segment
            subprocess.run([
                'ffmpeg', '-i', str(audio_path),
                '-ss', str(segment['start']),
                '-t', str(segment['end'] - segment['start']),
                '-ar', '44100', '-ac', '1',  # 44.1kHz mono
                '-y', str(temp_file)
            ], capture_output=True, check=True)
        
        # Concatenate segments
        output_path = Path(tempfile.mktemp(suffix=f'_speaker_{speaker_id}_clone.wav'))
        
        if len(temp_files) == 1:
            # Single file, just copy
            subprocess.run(['cp', str(temp_files[0]), str(output_path)], check=True)
        else:
            # Concatenate multiple files
            input_list = '|'.join(str(f) for f in temp_files)
            subprocess.run([
                'ffmpeg', '-i', f'concat:{input_list}',
                '-acodec', 'copy', '-y', str(output_path)
            ], capture_output=True, check=True)
        
        return output_path
        
    except Exception as e:
        print(f"  Error extracting audio for Speaker {speaker_id}: {e}")
        return None
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()

def clone_voice_elevenlabs(audio_path: Path, speaker_name: str) -> Optional[str]:
    """
    Clone a voice using ElevenLabs API.
    Returns voice_id if successful, None if failed.
    """
    try:
        # Convert to MP3 if needed (ElevenLabs prefers MP3)
        mp3_path = audio_path.with_suffix('.mp3')
        if not mp3_path.exists():
            subprocess.run([
                'ffmpeg', '-i', str(audio_path),
                '-acodec', 'libmp3lame', '-ar', '22050',
                '-y', str(mp3_path)
            ], capture_output=True, check=True)
        else:
            mp3_path = audio_path
        
        # Check file size (ElevenLabs has 10MB limit)
        file_size_mb = mp3_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 10:
            print(f"  Audio file too large ({file_size_mb:.1f}MB), cloning may fail")
        
        print(f"  Uploading {file_size_mb:.1f}MB audio sample...")
        
        # Prepare the request
        url = f"{ELEVENLABS_BASE_URL}/voices/add"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "name": speaker_name,
            "description": f"Cloned voice for dubbing - {speaker_name}"
        }
        
        with open(mp3_path, 'rb') as audio_file:
            files = {
                "files": audio_file
            }
            
            response = requests.post(url, headers=headers, data=data, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            voice_id = result.get('voice_id')
            print(f"  ✅ Voice cloned successfully: {voice_id}")
            return voice_id
        else:
            print(f"  ❌ Cloning failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ Cloning error: {e}")
        return None
    finally:
        # Clean up temporary MP3
        if mp3_path != audio_path and mp3_path.exists():
            mp3_path.unlink()

def delete_cloned_voice(voice_id: str) -> bool:
    """
    Delete a cloned voice from ElevenLabs.
    """
    try:
        url = f"{ELEVENLABS_BASE_URL}/voices/{voice_id}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        
        response = requests.delete(url, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to delete voice {voice_id}: {e}")
        return False

def clone_speaker_voices(segments: List[Dict], audio_path: Path, use_cloning: bool = False) -> Dict[int, Optional[str]]:
    """
    Main function to clone voices for all speakers.
    
    Args:
        segments: List of transcribed segments
        audio_path: Path to original audio file
        use_cloning: Whether to actually perform cloning
        
    Returns:
        Dictionary mapping speaker_id -> cloned_voice_id (or None if cloning failed)
    """
    print(f"🧬 Voice Cloning: {'Enabled' if use_cloning else 'Disabled'}")
    
    if not use_cloning:
        return {}
    
    # Get unique speakers
    speakers = set(segment['speaker'] for segment in segments)
    cloned_voices = {}
    
    print(f"Attempting to clone {len(speakers)} speaker(s)...")
    
    for speaker_id in speakers:
        print(f"\n🎤 Processing Speaker {speaker_id}:")
        
        # Extract audio for this speaker
        speaker_audio_path = extract_speaker_audio_for_cloning(segments, audio_path, speaker_id)
        
        if speaker_audio_path is None:
            print(f"  ⏭️  Skipping cloning for Speaker {speaker_id}")
            cloned_voices[speaker_id] = None
            continue
        
        # Clone the voice
        speaker_name = f"Speaker_{speaker_id}_Clone"
        voice_id = clone_voice_elevenlabs(speaker_audio_path, speaker_name)
        
        cloned_voices[speaker_id] = voice_id
        
        # Clean up temp audio file
        if speaker_audio_path.exists():
            speaker_audio_path.unlink()
    
    successful_clones = sum(1 for v in cloned_voices.values() if v is not None)
    print(f"\n📊 Cloning Summary: {successful_clones}/{len(speakers)} voices cloned successfully")
    
    return cloned_voices

def cleanup_cloned_voices(cloned_voices: Dict[int, Optional[str]]):
    """
    Clean up cloned voices from ElevenLabs after use.
    """
    voices_to_delete = [v for v in cloned_voices.values() if v is not None]
    
    if not voices_to_delete:
        return
    
    print(f"\n🧹 Cleaning up {len(voices_to_delete)} cloned voice(s)...")
    
    for voice_id in voices_to_delete:
        if delete_cloned_voice(voice_id):
            print(f"  ✅ Deleted voice {voice_id}")
        else:
            print(f"  ⚠️  Failed to delete voice {voice_id}")