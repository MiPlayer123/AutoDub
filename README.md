# AutoDub - Automatic Video Dubbing Pipeline

Automatically dub YouTube videos into different languages using AI-powered transcription, translation, and speech synthesis. This project also includes a web interface for easy use.

## Features

- **YouTube Download**: Download videos directly from YouTube URLs
- **Speech Recognition**: Transcribe audio with speaker diarization using Deepgram
- **Translation**: Translate content using OpenAI GPT-4
- **Speech Synthesis**: Generate natural-sounding speech using ElevenLabs
- **Audio Alignment**: Synchronize dubbed audio with original video timing
- **Multi-Speaker Support**: Different voices for different speakers
- **Web Interface**: A simple web UI for submitting dubbing jobs and tracking progress.
- **Real-time Progress**: Step-by-step updates via polling in the web UI.
- **Background Processing**: Non-blocking job execution for web requests.
- **Error Handling**: Clear error messages in the web UI.
- **Voice Cloning**: Default enabled for best quality dubbing (via web UI).
- **Background Preservation**: Keeps original background music/effects (via web UI).

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

### Web Interface

1. **Start the server:**
   ```bash
   python web_server.py
   ```

2. **Open your browser:**
   - **Web Interface:** http://localhost:8000/
   - **API Docs:** http://localhost:8000/docs

3. **Use the interface:**
   - Paste YouTube URL
   - Select language 
   - Choose options (Voice Clone, Background Preservation)
   - Click "Auto-Dub" 
   - Watch progress in real-time
   - Download result when complete

### Python API

```python
from autodub.main import autodub_pipeline

output_path = autodub_pipeline(
    youtube_url="https://youtube.com/watch?v=VIDEO_ID",
    target_language="es",
    output_name="my_dubbed_video"
)
```

## Supported Languages

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
├── web_pipeline.py     # Progress-tracked pipeline for web
└── config.py           # Configuration & API keys
web_server.py           # FastAPI server
web_static/
└── index.html         # Minimal frontend
outputs/                # Generated videos
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

- Job history and management for the web interface
- Batch processing for CLI and web
- Advanced UI improvements
- External API integrations
- Performance optimizations
- Quality adjustment settings

## Requirements

- Python 3.8+
- FFmpeg
- API Keys: Deepgram, OpenAI, ElevenLabs

## License

MIT