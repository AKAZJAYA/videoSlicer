from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from fastapi.staticfiles import StaticFiles
from app.slicer import process_video_async

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
