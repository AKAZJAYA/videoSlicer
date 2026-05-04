import os
import asyncio
from faster_whisper import WhisperModel

# Initialize model once globally to save load time. 
# Using "base" model for speed, running on CPU.
model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_video_sync(filepath: str):
    # Returns a list of segments
    segments, info = model.transcribe(filepath, word_timestamps=False)
    results = []
    for segment in segments:
        results.append({
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })
    return results

async def process_transcription_async(filepath: str):
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, transcribe_video_sync, filepath)
    return results
