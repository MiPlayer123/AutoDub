#!/usr/bin/env python3
"""
Web-optimized AutoDub pipeline with progress tracking
Wrapper around main_enhanced.py that provides progress updates for web interface
"""

from pathlib import Path
from typing import Optional, Callable

from .main_enhanced import LANGUAGE_MAP
from .pipeline.download import download_video
from .pipeline.separate import separate_audio
from .pipeline.transcribe import transcribe_audio
from .pipeline.speaker_profile import build_speaker_profiles
from .pipeline.voice_mapper import assign_unique_voices
from .pipeline.voice_clone import clone_speaker_voices, cleanup_cloned_voices
from .pipeline.translate import translate_segments
from .pipeline.synthesize_enhanced import synthesize_segments_enhanced, validate_voice_assignments
from .pipeline.align_simple import align_segments_simple
from .pipeline.mix_simple import mix_audio_simple
from .pipeline.mux import mux_video
from .config import TEMP_DIR, OUTPUT_DIR

def enhanced_autodub_pipeline_with_progress(
    youtube_url: str,
    target_language: str = 'es',
    output_name: Optional[str] = None,
    preserve_background: bool = True,
    diverse_voices: bool = True,
    voice_clone: bool = False,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Path:
    """
    Enhanced AutoDub pipeline with progress tracking for web interface.
    
    Args:
        youtube_url: YouTube video URL
        target_language: Target language code
        output_name: Output filename (without extension)
        preserve_background: Whether to preserve background audio
        diverse_voices: Whether to use different voices for different speakers
        voice_clone: Whether to enable voice cloning
        progress_callback: Function to call with progress updates (step, message)
        
    Returns:
        Path to the final dubbed video
    """
    def update_progress(step: int, message: str):
        if progress_callback:
            progress_callback(step, message)
        print(f"[Step {step}/9] {message}")
    
    try:
        update_progress(1, "Downloading video and extracting audio...")
        video_path, audio_path = download_video(youtube_url, output_name or "web_job")
        
        update_progress(2, "Transcribing with speaker diarization...")
        segments = transcribe_audio(audio_path)
        
        if preserve_background:
            update_progress(3, "Separating vocals from background...")
            vocals_path, background_path = separate_audio(audio_path, use_separation=True)
        else:
            update_progress(3, "Skipping source separation...")
            vocals_path = None
            background_path = None
        
        if not segments:
            raise Exception("No speech segments detected in the video")
        
        # Check speakers
        unique_speakers = set(segment['speaker'] for segment in segments)
        update_progress(4, f"Detected {len(unique_speakers)} unique speaker(s)")
        
        # Voice cloning
        cloned_voices = {}
        if voice_clone:
            update_progress(4, "Cloning voices...")
            cloned_voices = clone_speaker_voices(segments, audio_path, use_cloning=True)
        
        # Speaker analysis and voice assignment
        if diverse_voices and len(unique_speakers) > 1:
            update_progress(5, "Building speaker profiles...")
            speaker_profiles = build_speaker_profiles(segments, vocals_path if preserve_background else audio_path)
            
            update_progress(5, "Assigning unique voices...")
            voice_assignments = assign_unique_voices(speaker_profiles)
        else:
            update_progress(5, "Using default voice assignment...")
            from .config import DEFAULT_VOICE_ID
            voice_assignments = {}
            for speaker in unique_speakers:
                voice_assignments[speaker] = DEFAULT_VOICE_ID
        
        # ALWAYS override with cloned voices if available (regardless of diverse_voices setting)
        if cloned_voices:
            print(f"Overriding voice assignments with {len(cloned_voices)} cloned voices...")
            for speaker_id, cloned_voice_id in cloned_voices.items():
                if cloned_voice_id is not None:
                    voice_assignments[speaker_id] = cloned_voice_id
                    print(f"  Speaker {speaker_id} -> Using cloned voice ({cloned_voice_id[:12]}...)")
        
        # Always validate final assignments
        validate_voice_assignments(voice_assignments)
        
        # Translation
        lang_name, lang_code = LANGUAGE_MAP.get(target_language, (target_language, target_language))
        update_progress(6, f"Translating {len(segments)} segments to {lang_name}...")
        segments = translate_segments(segments, lang_name)
        
        # Synthesis
        update_progress(7, "Multi-speaker synthesis...")
        segments = synthesize_segments_enhanced(
            segments, 
            voice_assignments, 
            lang_code,
            speaker_profiles if diverse_voices and len(unique_speakers) > 1 else {}
        )
        
        # Alignment and mixing
        update_progress(8, "Aligning audio segments...")
        dubbed_audio_path = align_segments_simple(segments)
        
        if preserve_background and background_path:
            update_progress(8, "Mixing with preserved background...")
            final_audio_path = mix_audio_simple(dubbed_audio_path, background_path)
        else:
            final_audio_path = dubbed_audio_path
        
        update_progress(9, "Creating final dubbed video...")
        output_path = mux_video(video_path, final_audio_path, output_name or "web_output")
        
        # Cleanup
        if cloned_voices:
            cleanup_cloned_voices(cloned_voices)
        
        update_progress(9, "Completed successfully!")
        return output_path
        
    except Exception as e:
        update_progress(9, f"❌ Failed: {e}")
        raise