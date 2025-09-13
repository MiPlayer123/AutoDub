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
    
    print(f"Transcribed {len(segments)} segments")
    return segments