import os
import uuid
import asyncio

def format_srt_time(seconds):
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(captions, output_filepath):
    with open(output_filepath, "w", encoding="utf-8") as f:
        for i, cap in enumerate(captions):
            start = format_srt_time(float(cap["start"]))
            end = format_srt_time(float(cap["end"]))
            text = cap["text"]
            f.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")

async def burn_captions_async(video_path, captions, output_dir):
    temp_id = str(uuid.uuid4())
    srt_filename = f"{temp_id}.srt"
    srt_filepath = os.path.join(output_dir, srt_filename)
    
    output_filename = f"{temp_id}_captioned.mp4"
    output_filepath = os.path.join(output_dir, output_filename)
    
    # 1. Generate SRT file
    generate_srt(captions, srt_filepath)
    
    # We must escape the path for ffmpeg filter
    escaped_srt_path = srt_filepath.replace("\\", "/").replace(":", "\\:")
    
    # Beautiful, modern TikTok-style captions: Bold, white text, black outline, centered at bottom
    style = "Alignment=2,OutlineColour=&H100000000,BorderStyle=1,Outline=2,Shadow=0,Fontsize=22,PrimaryColour=&H00FFFFFF,Bold=-1,MarginV=60"
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vf", f"subtitles={escaped_srt_path}:force_style='{style}'",
        "-c:v", "libx264",
        "-c:a", "copy", # Audio doesn't need to be re-encoded
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
        raise Exception(f"Failed to burn captions: {stderr.decode()[-200:]}")
        
    # Clean up SRT
    if os.path.exists(srt_filepath):
        os.remove(srt_filepath)
        
    return output_filename
