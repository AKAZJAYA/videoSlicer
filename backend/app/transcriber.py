import os
import asyncio
from faster_whisper import WhisperModel

# Initialize model once globally to save load time. 
# Using "tiny" model for speed, running on CPU.
model = WhisperModel("tiny", device="cpu", compute_type="int8")

def transcribe_video_sync(filepath: str):
    # Returns a list of segments
    segments, info = model.transcribe(filepath, word_timestamps=True)
    results = []
    for segment in segments:
        words = []
        if segment.words:
            for w in segment.words:
                words.append({
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "word": w.word.strip()
                })

        results.append({
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "words": words
        })
    return results

async def process_transcription_async(filepath: str):
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, transcribe_video_sync, filepath)
    return results
