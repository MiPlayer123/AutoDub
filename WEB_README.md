# AutoDub Web Interface

🎬 **Phase 1 Complete** - FastAPI wrapper with minimal HTML frontend

## Quick Start

1. **Start the server:**
   ```bash
   ./start_web_server.sh
   # OR
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

## Features ✅

- **Simple UI**: Paste URL → Pick language → Click button → Get video
- **Real-time Progress**: Step-by-step updates via polling
- **Background Processing**: Non-blocking job execution
- **Error Handling**: Clear error messages
- **Voice Cloning**: Default enabled for best quality
- **Background Preservation**: Keeps original music/effects

## API Endpoints

### POST `/dub`
Create a new dubbing job
```bash
curl -X POST "http://localhost:8000/dub" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "youtube_url=https://youtube.com/watch?v=...&language=es&voice_clone=true"
```

### GET `/jobs/{job_id}`
Check job status and progress
```bash
curl "http://localhost:8000/jobs/abc123"
```

### GET `/outputs/{filename}`
Download completed videos

## File Structure

```
├── web_server.py           # FastAPI server
├── autodub/
│   ├── web_pipeline.py     # Progress-tracked pipeline
│   └── main_enhanced.py    # Original CLI (unchanged)
├── web_static/
│   └── index.html         # Minimal frontend
└── outputs/               # Generated videos
```

## What's Working

✅ **Existing CLI** - All original functionality preserved  
✅ **Web API** - FastAPI wrapper with job queue  
✅ **Progress Tracking** - Real-time step updates  
✅ **Frontend** - Ultra-simple interface as requested  
✅ **Voice Cloning** - Default enabled with fallbacks  
✅ **Background Audio** - Preserved without ducking  
✅ **Error Handling** - Clean error messages  
✅ **File Serving** - Direct video playback and download  

## Next Steps (Phase 2+)

- Job history and management
- Batch processing
- Advanced UI improvements  
- External API integrations
- Performance optimizations

---

**Ready to use!** No breaking changes to existing CLI functionality.