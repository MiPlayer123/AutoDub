# AutoDub - Automatic Video Dubbing Pipeline

Automatically dub YouTube videos into different languages using AI-powered transcription, translation, and speech synthesis.

## Features

- **YouTube Download**: Download videos directly from YouTube URLs
- **Speech Recognition**: Transcribe audio with speaker diarization using Deepgram
- **Translation**: Translate content using OpenAI GPT-4
- **Speech Synthesis**: Generate natural-sounding speech using ElevenLabs
- **Audio Alignment**: Synchronize dubbed audio with original video timing
- **Multi-Speaker Support**: Different voices for different speakers

## Installation

1. Install system dependencies:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up API keys in `.env`:
```env
ELEVENLABS_API_KEY=your_elevenlabs_key
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
```

## Usage

### Command Line Interface

```bash
# Dub to Spanish (default)
python -m autodub.main https://youtube.com/watch?v=VIDEO_ID

# Dub to French
python -m autodub.main https://youtube.com/watch?v=VIDEO_ID --lang fr

# Custom output name
python -m autodub.main https://youtube.com/watch?v=VIDEO_ID --lang de --output my_video
```

### Supported Languages

- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- `ar` - Arabic
- `hi` - Hindi

### Python API

```python
from autodub.main import autodub_pipeline

output_path = autodub_pipeline(
    youtube_url="https://youtube.com/watch?v=VIDEO_ID",
    target_language="es",
    output_name="my_dubbed_video"
)
```

## Pipeline Architecture

1. **Download**: Downloads video and extracts audio using yt-dlp
2. **Transcribe**: Transcribes audio with speaker labels using Deepgram
3. **Translate**: Translates each segment using OpenAI
4. **Synthesize**: Generates speech for each segment using ElevenLabs
5. **Align**: Adjusts audio timing to match original video
6. **Mux**: Combines dubbed audio with original video

## Project Structure

```
autodub/
├── pipeline/
│   ├── download.py      # YouTube download & audio extraction
│   ├── transcribe.py    # Deepgram ASR integration
│   ├── translate.py     # OpenAI translation
│   ├── synthesize.py    # ElevenLabs TTS
│   ├── align.py         # Audio timing alignment
│   └── mux.py          # Video/audio muxing
├── main.py             # CLI entry point
└── config.py           # Configuration & API keys
```

## Output

Dubbed videos are saved to the `outputs/` directory with the format:
`{output_name}_dubbed.mp4`

## Testing

Run the test script with a sample video:

```bash
python test_pipeline.py
```

## Future Enhancements

- [ ] Source separation to preserve background music
- [ ] Voice cloning for original speaker voices
- [ ] FastAPI server for web interface
- [ ] Real-time progress tracking
- [ ] Batch processing support
- [ ] Quality adjustment settings

## Requirements

- Python 3.8+
- FFmpeg
- API Keys: Deepgram, OpenAI, ElevenLabs

## License

MIT