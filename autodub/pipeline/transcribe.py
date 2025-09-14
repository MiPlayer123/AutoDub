from pathlib import Path
from typing import List, Dict
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from ..config import DEEPGRAM_API_KEY

def transcribe_audio(audio_path: Path) -> List[Dict]:
    """
    Transcribe audio using Deepgram with speaker diarization.
    Returns list of segments with speaker labels.
    """
    print(f"Transcribing audio: {audio_path}")
    
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
    
    with open(audio_path, 'rb') as audio:
        buffer_data = audio.read()
    
    payload: FileSource = {
        "buffer": buffer_data,
    }
    
    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
        utterances=True,
        diarize=True,
        punctuate=True,
        language="en"
        # Removed multichannel to avoid duplicates
    )
    
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
    
    segments = []
    if hasattr(response, 'results') and response.results.utterances:
        for utterance in response.results.utterances:
            segment = {
                'start': utterance.start,
                'end': utterance.end,
                'text': utterance.transcript,
                'speaker': utterance.speaker,
                'confidence': utterance.confidence
            }
            segments.append(segment)
            print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] Speaker {segment['speaker']}: {segment['text'][:50]}...")
    
    # Deduplicate segments (remove duplicates with same timing and speaker)
    segments = deduplicate_segments(segments)
    
    print(f"Transcribed {len(segments)} segments")
    return segments

def deduplicate_segments(segments: List[Dict]) -> List[Dict]:
    """
    Remove duplicate segments with same start time, end time, and speaker.
    Keep the one with highest confidence.
    """
    if not segments:
        return segments
    
    # Group by (start, end, speaker)
    segment_groups = {}
    for segment in segments:
        key = (round(segment['start'], 2), round(segment['end'], 2), segment['speaker'])
        if key not in segment_groups:
            segment_groups[key] = []
        segment_groups[key].append(segment)
    
    # Keep best segment from each group
    deduplicated = []
    duplicates_removed = 0
    
    for key, group in segment_groups.items():
        if len(group) > 1:
            # Multiple segments with same timing - keep highest confidence
            best_segment = max(group, key=lambda x: x.get('confidence', 0))
            deduplicated.append(best_segment)
            duplicates_removed += len(group) - 1
        else:
            deduplicated.append(group[0])
    
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate segments")
    
    # Sort by start time
    deduplicated.sort(key=lambda x: x['start'])
    return deduplicated