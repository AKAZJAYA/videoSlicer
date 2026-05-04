import os
import uuid
import asyncio
import random
from yt_dlp import YoutubeDL

# Use a semaphore to prevent YouTube from throttling us if the user requests 10 slices at once
semaphore = asyncio.Semaphore(3)

async def slice_single_stream(video_url, start_time, slice_length, output_dir):
    async with semaphore:
        temp_id = str(uuid.uuid4())
        output_filename = f"{temp_id}_slice.mp4"
        output_filepath = os.path.join(output_dir, output_filename)
        
        # FFmpeg connects directly to the stream, seeks to the exact start_time, 
        # and downloads ONLY the seconds we need.
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", video_url,
            "-t", str(slice_length),
            "-vf", "crop=ih*9/16:ih",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            output_filepath
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print("FFmpeg Error:", stderr.decode())
            raise Exception(f"Failed to process video slice: {stderr.decode()[-200:]}")
            
        return output_filename

def get_video_stream(url):
    # 'best' gets a single file with both video and audio up to 720p. 
    # This is critical because requesting separate video and audio streams 
    # simultaneously causes FFmpeg to download huge chunks of the video trying to sync them!
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

async def process_video_async(url: str, duration_str: str, slice_count: int, output_dir: str):
    # 1. Extract the direct streaming URL (No downloading the video here!)
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_video_stream, url)
    
    video_url = info.get('url')
    if not video_url:
        raise Exception("Could not extract video stream URL")

    # 2. Determine duration
    slice_length = 30
    if duration_str == '15-30s': slice_length = 30
    elif duration_str == '30-45s': slice_length = 45
    elif duration_str == '45-60s': slice_length = 60
    elif duration_str == '60-120s': slice_length = 120
    elif duration_str == '150s': slice_length = 150
    elif duration_str == '180s': slice_length = 180

    video_duration = info.get('duration', 600) # fallback
    
    # Generate random start times avoiding overlap
    valid_starts = []
    attempts = 0
    max_start = max(11, int(video_duration - slice_length - 10))
    
    while len(valid_starts) < slice_count and attempts < 1000:
        st = random.randint(10, max_start)
        overlap = False
        for v in valid_starts:
            if abs(st - v) < slice_length + 5: # 5 sec buffer
                overlap = True
                break
        if not overlap:
            valid_starts.append(st)
        attempts += 1
        
    # 3. Stream and slice concurrently (limited by semaphore)
    tasks = []
    for st in valid_starts:
        tasks.append(slice_single_stream(video_url, st, slice_length, output_dir))
        
    filenames = await asyncio.gather(*tasks)
    return filenames
