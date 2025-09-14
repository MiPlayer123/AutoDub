#!/usr/bin/env python3
"""
FastAPI Web Server for AutoDub
Provides REST API wrapper around the enhanced autodub pipeline
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import threading
import traceback

from fastapi import FastAPI, HTTPException, BackgroundTasks, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydub import AudioSegment
import uvicorn

from autodub.main_enhanced import LANGUAGE_MAP
from autodub.web_pipeline import enhanced_autodub_pipeline_with_progress

app = FastAPI(title="AutoDub API", version="1.0.0")

# Job storage (in production, use Redis/database)
jobs: Dict[str, Dict[str, Any]] = {}

# Background task runner
def run_autodub_pipeline(
    job_id: str,
    youtube_url: str,
    language: str,
    voice_clone: bool,
    preserve_background: bool
):
    """Run the autodub pipeline in background thread"""
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # Progress callback function
        def update_progress(step: int, message: str):
            jobs[job_id].update({
                "progress": step,
                "total_steps": 9,
                "current_step": message,
                "status": "processing"
            })
            print(f"[{job_id}] Step {step}/9: {message}")
        
        # Run the pipeline with progress tracking
        output_path = enhanced_autodub_pipeline_with_progress(
            youtube_url=youtube_url,
            target_language=language,
            output_name=f"job_{job_id}",
            preserve_background=preserve_background,
            diverse_voices=True,
            voice_clone=voice_clone,
            progress_callback=update_progress
        )
        
        # Success
        jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "output_path": str(output_path),
            "output_url": f"/outputs/{output_path.name}",
            "progress": 9,
            "current_step": "✅ Completed successfully!"
        })
        
    except Exception as e:
        # Error handling
        error_msg = str(e)
        traceback.print_exc()
        
        jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": error_msg,
            "current_step": f"❌ Failed: {error_msg}"
        })

@app.post("/dub")
async def create_dub_job(
    background_tasks: BackgroundTasks,
    youtube_url: str = Form(...),
    language: str = Form("es"),
    voice_clone: bool = Form(True),
    preserve_background: bool = Form(True)
):
    """Create a new dubbing job"""
    
    # Validate inputs
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")
    
    if language not in LANGUAGE_MAP:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language. Available: {list(LANGUAGE_MAP.keys())}"
        )
    
    # Create job
    job_id = str(uuid.uuid4())[:8]  # Short ID
    
    jobs[job_id] = {
        "job_id": job_id,
        "youtube_url": youtube_url,
        "language": language,
        "voice_clone": voice_clone,
        "preserve_background": preserve_background,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "total_steps": 9,
        "current_step": "Queued for processing..."
    }
    
    # Start background task
    background_tasks.add_task(
        run_autodub_pipeline,
        job_id,
        youtube_url,
        language,
        voice_clone,
        preserve_background
    )
    
    return {"job_id": job_id}

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/jobs")
async def list_jobs():
    """List all jobs (for debugging)"""
    return {"jobs": jobs}

# Serve output files
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=output_dir), name="outputs")

# Serve static frontend files
static_dir = Path("web_static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML interface"""
    html_path = Path("web_static/index.html")
    if html_path.exists():
        return FileResponse(html_path)
    else:
        # Return basic HTML if no file exists yet
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AutoDub - Web Interface</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>🎬 AutoDub</h1>
            <p>Web interface loading...</p>
            <p>API is running at <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    print("🚀 Starting AutoDub Web Server...")
    print("📡 API Documentation: http://localhost:8000/docs")
    print("🌐 Web Interface: http://localhost:8000/")
    
    uvicorn.run("web_server:app", host="0.0.0.0", port=8000, reload=True)