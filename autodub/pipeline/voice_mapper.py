from typing import Dict, List
import random

# Expanded voice pool with gender and characteristics
VOICE_POOL = {
    # Male voices
    'male_1': {
        'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold - mature male
        'gender': 'male',
        'age_range': 'mature',
        'tone': 'authoritative'
    },
    'male_2': {
        'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - young male
        'gender': 'male', 
        'age_range': 'young',
        'tone': 'conversational'
    },
    'male_3': {
        'voice_id': 'ErXwobaYiN019PkySvjV',  # Antoni - warm male
        'gender': 'male',
        'age_range': 'middle',
        'tone': 'warm'
    },
    'male_4': {
        'voice_id': 'CYw3kZ02Hs0563khs1Fj',  # Dave - casual male
        'gender': 'male',
        'age_range': 'middle', 
        'tone': 'casual'
    },
    
    # Female voices
    'female_1': {
        'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - professional female
        'gender': 'female',
        'age_range': 'mature',
        'tone': 'professional'
    },
    'female_2': {
        'voice_id': 'ThT5KcBeYPX3keUQqHPh',  # Dorothy - pleasant female
        'gender': 'female',
        'age_range': 'middle',
        'tone': 'pleasant'
    },
    'female_3': {
        'voice_id': 'AZnzlk1XvdvUeBnXmlld',  # Domi - energetic female
        'gender': 'female',
        'age_range': 'young',
        'tone': 'energetic'
    },
    'female_4': {
        'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Bella - soft female
        'gender': 'female',
        'age_range': 'young',
        'tone': 'soft'
    },
    
    # Neutral voices (for ambiguous cases)
    'neutral_1': {
        'voice_id': 'flq6f7yk4E4fJM5XTYuZ',  # Michael - neutral
        'gender': 'neutral',
        'age_range': 'middle',
        'tone': 'neutral'
    },
    'neutral_2': {
        'voice_id': 'TxGEqnHWrfWFTfGW9XjX',  # Josh - neutral
        'gender': 'neutral', 
        'age_range': 'middle',
        'tone': 'neutral'
    }
}

def score_voice_match(speaker_profile: Dict, voice_info: Dict) -> float:
    """
    Score how well a voice matches a speaker profile.
    Higher score = better match. Prefer male voices as default.
    """
    score = 0.0
    
    # Prefer male voices (override gender detection)
    if voice_info['gender'] == 'male':
        score += 15.0  # Strong preference for male voices
    elif voice_info['gender'] == 'neutral':
        score += 8.0   # Neutral is second choice
    else:
        score += 3.0   # Female voices as fallback
    
    # Pitch-based matching
    mean_pitch = speaker_profile.get('mean_pitch', 150)
    if voice_info['gender'] == 'male':
        # Male voices work better for lower pitches
        if mean_pitch < 165:
            score += 3.0
        else:
            score -= 1.0
    elif voice_info['gender'] == 'female':
        # Female voices work better for higher pitches  
        if mean_pitch > 200:
            score += 3.0
        else:
            score -= 1.0
    
    # Prefer diverse tones
    score += random.uniform(-0.5, 0.5)  # Small random factor for variety
    
    return score

def assign_unique_voices(speaker_profiles: Dict[int, Dict], used_voices: List[str] = None) -> Dict[int, str]:
    """
    Assign unique, appropriate voices to each speaker based on their profiles.
    
    Args:
        speaker_profiles: Dictionary mapping speaker_id -> characteristics
        used_voices: List of voice IDs already assigned (for avoiding conflicts)
        
    Returns:
        Dictionary mapping speaker_id -> voice_id
    """
    print("Assigning voices to speakers...")
    
    if used_voices is None:
        used_voices = []
    
    assignments = {}
    available_voices = list(VOICE_POOL.keys())
    
    # Sort speakers by total speaking time (prioritize main speakers)
    speakers_by_duration = sorted(
        speaker_profiles.items(),
        key=lambda x: x[1].get('total_duration', 0),
        reverse=True
    )
    
    print(f"Speaker priority by duration: {[f'Speaker {sid}' for sid, _ in speakers_by_duration]}")
    
    for speaker_id, profile in speakers_by_duration:
        print(f"\nAssigning voice for Speaker {speaker_id}:")
        print(f"  Profile: {profile['estimated_gender']} "
              f"({profile['mean_pitch']:.1f}Hz, "
              f"{profile['total_duration']:.1f}s total)")
        
        # Score all available voices
        voice_scores = []
        for voice_name in available_voices:
            if voice_name not in used_voices:  # Skip already assigned voices
                voice_info = VOICE_POOL[voice_name]
                score = score_voice_match(profile, voice_info)
                voice_scores.append((voice_name, voice_info, score))
        
        if not voice_scores:
            # Fallback if no voices available (shouldn't happen with our pool size)
            print(f"  Warning: No available voices, using default")
            voice_id = '21m00Tcm4TlvDq8ikWAM'  # Rachel as fallback
        else:
            # Pick the best matching voice
            voice_scores.sort(key=lambda x: x[2], reverse=True)
            best_voice_name, best_voice_info, best_score = voice_scores[0]
            voice_id = best_voice_info['voice_id']
            
            print(f"  Best match: {best_voice_name} "
                  f"({best_voice_info['gender']} {best_voice_info['tone']}, score: {best_score:.1f})")
            
            # Mark this voice as used
            used_voices.append(best_voice_name)
            if best_voice_name in available_voices:
                available_voices.remove(best_voice_name)
        
        assignments[speaker_id] = voice_id
    
    print(f"\nFinal voice assignments:")
    for speaker_id, voice_id in assignments.items():
        voice_name = next((name for name, info in VOICE_POOL.items() if info['voice_id'] == voice_id), 'unknown')
        print(f"  Speaker {speaker_id} -> {voice_name} ({voice_id})")
    
    return assignments

def get_voice_settings_for_speaker(speaker_profile: Dict) -> Dict:
    """
    Get optimized voice settings based on speaker characteristics.
    """
    settings = {
        "stability": 0.5,
        "similarity_boost": 0.8,
        "style": 0.0,
        "use_speaker_boost": True
    }
    
    # Adjust stability based on speaking patterns
    segment_count = speaker_profile.get('segment_count', 1)
    if segment_count > 10:  # Frequent speaker, use more stability
        settings["stability"] = 0.7
    
    # Adjust similarity boost based on confidence
    gender_confidence = speaker_profile.get('gender_confidence', 0.5)
    settings["similarity_boost"] = 0.6 + (0.4 * gender_confidence)
    
    return settings