import os
import uuid
import asyncio
import random
from yt_dlp import YoutubeDL

async def slice_single_video(video_url, audio_url, start_time, slice_length, output_dir):
    temp_id = str(uuid.uuid4())
    output_filename = f"{temp_id}_slice.mp4"
    output_filepath = os.path.join(output_dir, output_filename)
    
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_time),
        "-i", video_url,
    ]
    
    if audio_url and audio_url != video_url:
        cmd.extend([
            "-ss", str(start_time),
            "-i", audio_url
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

def get_video_info(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

async def process_video_async(url: str, duration_str: str, slice_count: int, output_dir: str):
    # 1. Get Stream URLs using yt-dlp in executor to not block async loop
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_video_info, url)
    
    video_url = None
    audio_url = None
    
    if 'requested_formats' in info:
        for f in info['requested_formats']:
            if f.get('vcodec') != 'none':
                video_url = f['url']
            elif f.get('acodec') != 'none':
                audio_url = f['url']
    else:
        video_url = info['url']
        audio_url = info['url']
        
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

    video_duration = info.get('duration', 600) # fallback to 10 mins if not found
    
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
        
    # 3. Process all slices concurrently
    tasks = []
    for st in valid_starts:
        tasks.append(slice_single_video(video_url, audio_url, st, slice_length, output_dir))
        
    filenames = await asyncio.gather(*tasks)
    return filenames
