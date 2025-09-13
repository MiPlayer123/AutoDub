#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Optional

from .pipeline.download import download_video
from .pipeline.transcribe import transcribe_audio
from .pipeline.translate import translate_segments
from .pipeline.synthesize import synthesize_segments
from .pipeline.align_improved import align_segments
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

def autodub_pipeline(
    youtube_url: str,
    target_language: str = 'es',
    output_name: Optional[str] = None
) -> Path:
    """
    Complete autodub pipeline: download -> transcribe -> translate -> synthesize -> align -> mux
    """
    print(f"\n{'='*60}")
    print(f"AutoDub Pipeline - Dubbing to {LANGUAGE_MAP.get(target_language, (target_language, target_language))[0]}")
    print(f"{'='*60}\n")
    
    try:
        print("[Step 1/6] Downloading video and extracting audio...")
        video_path, audio_path = download_video(youtube_url, output_name or "input")
        
        print("\n[Step 2/6] Transcribing audio with speaker detection...")
        segments = transcribe_audio(audio_path)
        
        if not segments:
            raise Exception("No speech segments detected in the video")
        
        lang_name, lang_code = LANGUAGE_MAP.get(target_language, (target_language, target_language))
        print(f"\n[Step 3/6] Translating {len(segments)} segments to {lang_name}...")
        segments = translate_segments(segments, lang_name)
        
        print(f"\n[Step 4/6] Synthesizing speech in {lang_name}...")
        segments = synthesize_segments(segments, lang_code)
        
        print("\n[Step 5/6] Aligning dubbed audio to original timing...")
        dubbed_audio_path = align_segments(segments)
        
        print("\n[Step 6/6] Creating final dubbed video...")
        output_path = mux_video(video_path, dubbed_audio_path, output_name or "output")
        
        print(f"\n{'='*60}")
        print(f"✅ Success! Dubbed video created at:")
        print(f"   {output_path}")
        print(f"{'='*60}\n")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        raise

def main():
    parser = argparse.ArgumentParser(
        description='AutoDub - Automatic video dubbing pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m autodub.main https://youtube.com/watch?v=... --lang es
  python -m autodub.main https://youtu.be/... --lang fr --output my_video
  
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
    
    args = parser.parse_args()
    
    try:
        autodub_pipeline(args.url, args.lang, args.output)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nPipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()