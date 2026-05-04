from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from fastapi.staticfiles import StaticFiles
from app.slicer import process_video_async
from app.transcriber import process_transcription_async
from app.caption_burner import burn_captions_async

app = FastAPI(title="Video Slicer API")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only, update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SliceRequest(BaseModel):
    url: str
    duration: str
    sliceCount: int = 1

class TranscribeRequest(BaseModel):
    video_url: str

class BurnCaptionsRequest(BaseModel):
    video_url: str
    captions: list

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Video Slicer Backend is running."}

@app.post("/api/slice")
async def slice_video(request: SliceRequest):
    try:
        filenames = await process_video_async(request.url, request.duration, request.sliceCount, STATIC_DIR)
        video_urls = [f"http://localhost:8001/static/{f}" for f in filenames]
        return {
            "status": "success",
            "message": f"Successfully generated {len(video_urls)} slices!",
            "video_urls": video_urls
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/transcribe")
async def transcribe_video(request: TranscribeRequest):
    try:
        # Extract the filename from the end of the URL
        filename = request.video_url.split("/")[-1]
        filepath = os.path.join(STATIC_DIR, filename)
        
        if not os.path.exists(filepath):
            return {"status": "error", "message": "File not found on server"}
            
        segments = await process_transcription_async(filepath)
        return {
            "status": "success",
            "segments": segments
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/burn-captions")
async def burn_captions(request: BurnCaptionsRequest):
    try:
        filename = request.video_url.split("/")[-1]
        filepath = os.path.join(STATIC_DIR, filename)
        
        if not os.path.exists(filepath):
            return {"status": "error", "message": "Video file not found on server"}
            
        new_filename = await burn_captions_async(filepath, request.captions, STATIC_DIR)
        
        return {
            "status": "success",
            "message": "Captions burned successfully!",
            "video_url": f"http://localhost:8001/static/{new_filename}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
