import requests
from pathlib import Path
from typing import List, Dict
from ..config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL, DEFAULT_VOICE_ID, TEMP_DIR

VOICE_MAP = {
    0: "21m00Tcm4TlvDq8ikWAM",  # Rachel (female)
    1: "VR6AewLTigWG4xSOukaG",  # Arnold (male)
    2: "pNInz6obpgDQGcFmaJgB",  # Adam (male)
    3: "ThT5KcBeYPX3keUQqHPh",  # Dorothy (female)
}

def synthesize_segments(segments: List[Dict], target_language_code: str = "es") -> List[Dict]:
    """
    Synthesize speech for each translated segment using ElevenLabs.
    Returns segments with audio file paths added.
    """
    print(f"Synthesizing {len(segments)} segments")
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    for i, segment in enumerate(segments):
        try:
            voice_id = VOICE_MAP.get(segment.get('speaker', 0), DEFAULT_VOICE_ID)
            
            url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
            
            data = {
                "text": segment.get('text_translated', segment['text']),
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                audio_path = TEMP_DIR / f"segment_{i:04d}.mp3"
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                segment['audio_path'] = audio_path
                print(f"Synthesized segment {i+1}/{len(segments)}: {audio_path.name}")
            else:
                print(f"Error synthesizing segment {i}: {response.status_code} - {response.text}")
                segment['audio_path'] = None
                
        except Exception as e:
            print(f"Synthesis error for segment {i}: {e}")
            segment['audio_path'] = None
    
    return segments