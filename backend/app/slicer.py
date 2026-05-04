import os
import uuid
import asyncio
import random
import time
from yt_dlp import YoutubeDL

# Semaphore to prevent throttling
semaphore = asyncio.Semaphore(3)

async def slice_single_stream(video_url, audio_url, start_time, slice_length, output_dir):
    async with semaphore:
        temp_id = str(uuid.uuid4())
        output_filename = f"{temp_id}_slice.mp4"
        output_filepath = os.path.join(output_dir, output_filename)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", video_url,
        ]
        
        # If we have separate high-quality video and audio streams, we map them both
        if audio_url and audio_url != video_url:
            cmd.extend([
                "-ss", str(start_time),
                "-i", audio_url,
                "-map", "0:v:0",
                "-map", "1:a:0"
            ])
            
        cmd.extend([
            "-t", str(slice_length),
            "-vf", "crop=ih*9/16:ih",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            output_filepath
        ])
        
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
    # Ask for up to 1080p video, and separate high-quality audio
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

def cleanup_old_files(output_dir):
    # Delete files older than 1 hour to prevent filling up storage
    now = time.time()
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        if os.path.isfile(filepath):
            if os.stat(filepath).st_mtime < now - 3600:
                try:
                    os.remove(filepath)
                except:
                    pass

async def process_video_async(url: str, duration_str: str, slice_count: int, output_dir: str):
    loop = asyncio.get_event_loop()
    
    # Background cleanup of old static files
    await loop.run_in_executor(None, cleanup_old_files, output_dir)
    
    # 1. Extract stream info
    info = await loop.run_in_executor(None, get_video_stream, url)
    
    video_url = None
    audio_url = None
    
    # Handle the DASH streams properly to get high quality 720p/1080p
    if 'requested_formats' in info:
        for f in info['requested_formats']:
            if f.get('vcodec') != 'none':
                video_url = f['url']
            elif f.get('acodec') != 'none':
                audio_url = f['url']
    else:
        video_url = info.get('url')
        audio_url = info.get('url')
        
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

    video_duration = info.get('duration', 600)
    
    valid_starts = []
    attempts = 0
    max_start = max(11, int(video_duration - slice_length - 10))
    
    while len(valid_starts) < slice_count and attempts < 1000:
        st = random.randint(10, max_start)
        overlap = False
        for v in valid_starts:
            if abs(st - v) < slice_length + 5:
                overlap = True
                break
        if not overlap:
            valid_starts.append(st)
        attempts += 1
        
    # 3. Stream and slice concurrently
    tasks = []
    for st in valid_starts:
        tasks.append(slice_single_stream(video_url, audio_url, st, slice_length, output_dir))
        
    filenames = await asyncio.gather(*tasks)
    return filenames
