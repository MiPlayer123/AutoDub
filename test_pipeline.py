#!/usr/bin/env python3
"""
Test script for AutoDub pipeline.
Uses a short YouTube video for quick testing.
"""

import sys
from autodub.main import autodub_pipeline

# Short test video (30 seconds): "What Is Python? | Python In 30 Seconds"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=Y8Tko2YC5hA"

def test_pipeline():
    print("Testing AutoDub Pipeline with a short video...")
    print(f"Video URL: {TEST_VIDEO_URL}")
    print("-" * 60)
    
    try:
        output_path = autodub_pipeline(
            youtube_url=TEST_VIDEO_URL,
            target_language='es',  # Spanish
            output_name='test_video'
        )
        print(f"\n✅ Test successful! Output: {output_path}")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)