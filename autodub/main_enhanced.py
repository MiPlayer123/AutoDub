#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Optional

from .pipeline.download import download_video
from .pipeline.separate import separate_audio
from .pipeline.transcribe import transcribe_audio
from .pipeline.speaker_profile import build_speaker_profiles
from .pipeline.voice_mapper import assign_unique_voices
from .pipeline.translate import translate_segments
from .pipeline.synthesize_enhanced import synthesize_segments_enhanced, validate_voice_assignments
from .pipeline.align_simple import align_segments_simple
from .pipeline.mix_simple import mix_audio_simple
from .pipeline.mux import mux_video
from .config import TEMP_DIR, OUTPUT_DIR

LANGUAGE_MAP = {
    'es': ('Spanish', 'es'),
    'fr': ('French', 'fr'),
    'de': ('German', 'de'),
    'it': ('Italian', 'it'),
    'pt': ('Portuguese', 'pt'),
    'ru': ('Russian', 'ru'),
    'ja': ('Japanese', 'ja'),
    'ko': ('Korean', 'ko'),
    'zh': ('Chinese', 'zh'),
    'ar': ('Arabic', 'ar'),
    'hi': ('Hindi', 'hi'),
}

def enhanced_autodub_pipeline(
    youtube_url: str,
    target_language: str = 'es',
    output_name: Optional[str] = None,
    preserve_background: bool = True,
    diverse_voices: bool = True
) -> Path:
    """
    Enhanced AutoDub pipeline with multi-speaker voice assignment and background preservation.
    
    Args:
        youtube_url: YouTube video URL
        target_language: Target language code
        output_name: Output filename (without extension)
        preserve_background: Whether to preserve background audio
        diverse_voices: Whether to use different voices for different speakers
    """
    print(f"\n{'='*70}")
    print(f"🎬 Enhanced AutoDub Pipeline - Multi-Speaker Dubbing")
    print(f"🎯 Target: {LANGUAGE_MAP.get(target_language, (target_language, target_language))[0]}")
    print(f"🎵 Background: {'Preserved' if preserve_background else 'Not preserved'}")
    print(f"🎭 Voice diversity: {'Enabled' if diverse_voices else 'Disabled'}")
    print(f"{'='*70}\n")
    
    try:
        # Step 1: Download
        print("📥 [Step 1/9] Downloading video and extracting audio...")
        video_path, audio_path = download_video(youtube_url, output_name or "enhanced_input")
        
        # Step 2: Transcription FIRST (before separation to preserve speaker info)
        print(f"\n🎙️ [Step 2/9] Transcribing with speaker diarization...")
        segments = transcribe_audio(audio_path)  # Always use original audio for transcription
        
        # Step 3: Source separation (after transcription)
        if preserve_background:
            print("\n🎵 [Step 3/9] Separating vocals from background...")
            vocals_path, background_path = separate_audio(audio_path, use_separation=True)
        else:
            print("\n⏭️ [Step 3/9] Skipping source separation...")
            vocals_path = None
            background_path = None
        
        if not segments:
            raise Exception("No speech segments detected in the video")
        
        # Check if multi-speaker content detected
        unique_speakers = set(segment['speaker'] for segment in segments)
        print(f"🗣️ Detected {len(unique_speakers)} unique speaker(s): {sorted(unique_speakers)}")
        
        # Step 4: Speaker analysis (if diverse voices enabled)
        if diverse_voices and len(unique_speakers) > 1:
            print(f"\n👥 [Step 4/9] Building speaker profiles...")
            speaker_profiles = build_speaker_profiles(segments, vocals_path if preserve_background else audio_path)
            
            print(f"\n🎭 [Step 5/9] Assigning unique voices...")
            voice_assignments = assign_unique_voices(speaker_profiles)
            validate_voice_assignments(voice_assignments)
        else:
            print(f"\n⏭️ [Step 4/9] Skipping speaker profiling (single speaker or diversity disabled)...")
            print(f"⏭️ [Step 5/9] Using default voice assignment...")
            speaker_profiles = {}
            # Use default male voice for all speakers
            from .config import DEFAULT_VOICE_ID
            voice_assignments = {speaker: DEFAULT_VOICE_ID for speaker in unique_speakers}
        
        # Step 6: Translation
        lang_name, lang_code = LANGUAGE_MAP.get(target_language, (target_language, target_language))
        print(f"\n🌍 [Step 6/9] Translating {len(segments)} segments to {lang_name}...")
        segments = translate_segments(segments, lang_name)
        
        # Step 7: Enhanced synthesis
        print(f"\n🗣️ [Step 7/9] Multi-speaker synthesis...")
        segments = synthesize_segments_enhanced(
            segments, 
            voice_assignments, 
            lang_code,
            speaker_profiles
        )
        
        # Step 8: Simple Alignment
        print("\n⏰ [Step 8/9] Aligning audio segments...")
        dubbed_audio_path = align_segments_simple(segments)
        
        # Step 9: Final mixing and video creation
        if preserve_background and background_path:
            print("\n🎵 [Step 9a/9] Mixing with preserved background...")
            final_audio_path = mix_audio_simple(dubbed_audio_path, background_path)
        else:
            final_audio_path = dubbed_audio_path
        
        print("\n🎬 [Step 9b/9] Creating final dubbed video...")
        output_path = mux_video(video_path, final_audio_path, output_name or "enhanced_output")
        
        # Success summary
        print(f"\n{'='*70}")
        print(f"✅ Enhanced pipeline completed successfully!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Statistics:")
        print(f"   • Total segments: {len(segments)}")
        print(f"   • Unique speakers: {len(unique_speakers)}")
        print(f"   • Voices used: {len(set(voice_assignments.values()))}")
        successful_segments = sum(1 for s in segments if s.get('synthesis_success', False))
        print(f"   • Synthesis success: {successful_segments}/{len(segments)} ({successful_segments/len(segments)*100:.1f}%)")
        print(f"   • Background preserved: {'Yes' if preserve_background else 'No'}")
        print(f"{'='*70}\n")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ Enhanced pipeline failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced AutoDub - Multi-speaker video dubbing pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m autodub.main_enhanced https://youtube.com/watch?v=... --lang es
  python -m autodub.main_enhanced https://youtu.be/... --lang fr --output my_video
  python -m autodub.main_enhanced https://youtu.be/... --lang de --preserve-background
  python -m autodub.main_enhanced https://youtu.be/... --lang es --no-diverse-voices
  
Supported languages:
  es - Spanish     fr - French      de - German
  it - Italian     pt - Portuguese  ru - Russian
  ja - Japanese    ko - Korean      zh - Chinese
  ar - Arabic      hi - Hindi
        """
    )
    
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument(
        '--lang', '-l',
        default='es',
        choices=list(LANGUAGE_MAP.keys()),
        help='Target language code (default: es)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output filename (without extension)'
    )
    parser.add_argument(
        '--preserve-background',
        action='store_true',
        default=True,
        help='Preserve original background music and effects (default: True)'
    )
    parser.add_argument(
        '--no-preserve-background',
        action='store_false',
        dest='preserve_background',
        help='Disable background preservation'
    )
    parser.add_argument(
        '--diverse-voices',
        action='store_true',
        default=True,
        help='Use different voices for different speakers (default: True)'
    )
    parser.add_argument(
        '--no-diverse-voices',
        action='store_false',
        dest='diverse_voices',
        help='Use same voice for all speakers'
    )
    
    args = parser.parse_args()
    
    try:
        enhanced_autodub_pipeline(
            args.url, 
            args.lang, 
            args.output,
            args.preserve_background,
            args.diverse_voices
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nEnhanced pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()