import requests
from pathlib import Path
from typing import List, Dict
from ..config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL, TEMP_DIR
from .voice_mapper import get_voice_settings_for_speaker

def synthesize_segments_enhanced(
    segments: List[Dict], 
    voice_assignments: Dict[int, str], 
    target_language_code: str = "es",
    speaker_profiles: Dict[int, Dict] = None
) -> List[Dict]:
    """
    Enhanced synthesis with speaker-specific voice assignments and optimized settings.
    
    Args:
        segments: List of translated segments with speaker IDs
        voice_assignments: Dictionary mapping speaker_id -> voice_id  
        target_language_code: Target language code
        speaker_profiles: Optional speaker profiles for voice optimization
        
    Returns:
        Segments with audio file paths added
    """
    print(f"Enhanced synthesis: {len(segments)} segments with {len(voice_assignments)} unique voices")
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json", 
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    # Track synthesis stats
    synthesis_stats = {}
    for speaker_id in voice_assignments.keys():
        synthesis_stats[speaker_id] = {'segments': 0, 'success': 0, 'failed': 0}
    
    for i, segment in enumerate(segments):
        speaker_id = segment.get('speaker', 0)
        
        # Update stats
        if speaker_id in synthesis_stats:
            synthesis_stats[speaker_id]['segments'] += 1
        
        try:
            # Get assigned voice for this speaker
            voice_id = voice_assignments.get(speaker_id)
            if not voice_id:
                print(f"Warning: No voice assigned to speaker {speaker_id}, using default")
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel fallback
            
            # Get optimized settings for this speaker
            if speaker_profiles and speaker_id in speaker_profiles:
                voice_settings = get_voice_settings_for_speaker(speaker_profiles[speaker_id])
            else:
                voice_settings = {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            
            url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
            
            data = {
                "text": segment.get('text_translated', segment['text']),
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_settings
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                audio_path = TEMP_DIR / f"segment_{i:04d}.mp3"
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                
                segment['audio_path'] = audio_path
                segment['voice_id'] = voice_id
                segment['synthesis_success'] = True
                
                if speaker_id in synthesis_stats:
                    synthesis_stats[speaker_id]['success'] += 1
                
                # Show progress with speaker info
                speaker_info = f"Speaker {speaker_id}"
                if len(voice_assignments) > 1:  # Only show voice info if multiple speakers
                    voice_name = voice_id[:8] + "..."
                    speaker_info += f" ({voice_name})"
                
                print(f"✓ Segment {i+1}/{len(segments)}: {speaker_info}")
                
            else:
                print(f"✗ Segment {i+1}: HTTP {response.status_code} - {response.text[:100]}")
                segment['audio_path'] = None
                segment['synthesis_success'] = False
                
                if speaker_id in synthesis_stats:
                    synthesis_stats[speaker_id]['failed'] += 1
                
        except Exception as e:
            print(f"✗ Segment {i+1}: Error - {e}")
            segment['audio_path'] = None
            segment['synthesis_success'] = False
            
            if speaker_id in synthesis_stats:
                synthesis_stats[speaker_id]['failed'] += 1
    
    # Print synthesis summary
    print(f"\n📊 Synthesis Summary:")
    total_success = sum(stats['success'] for stats in synthesis_stats.values())
    total_segments = len(segments)
    print(f"   Overall: {total_success}/{total_segments} segments successful ({total_success/total_segments*100:.1f}%)")
    
    if len(synthesis_stats) > 1:
        print(f"   Per speaker:")
        for speaker_id, stats in synthesis_stats.items():
            voice_id = voice_assignments.get(speaker_id, "unknown")
            success_rate = stats['success'] / stats['segments'] * 100 if stats['segments'] > 0 else 0
            print(f"     Speaker {speaker_id}: {stats['success']}/{stats['segments']} segments ({success_rate:.1f}%) - {voice_id[:12]}...")
    
    return segments

def validate_voice_assignments(voice_assignments: Dict[int, str]) -> bool:
    """
    Validate that voice assignments are unique and valid.
    """
    if not voice_assignments:
        return False
    
    # Check for duplicate voice IDs (speakers should have unique voices)
    voice_ids = list(voice_assignments.values())
    if len(voice_ids) != len(set(voice_ids)):
        print("Warning: Duplicate voice assignments detected!")
        duplicates = [vid for vid in voice_ids if voice_ids.count(vid) > 1]
        print(f"Duplicate voices: {set(duplicates)}")
        return False
    
    print(f"✓ Voice assignments validated: {len(voice_assignments)} speakers with unique voices")
    return True