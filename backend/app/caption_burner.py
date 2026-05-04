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

def hex_to_ass_color(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        r, g, b = hex_str[0:2], hex_str[2:4], hex_str[4:6]
        return f"&H00{b}{g}{r}"
    return "&H00FFFFFF"

def build_ass_style(style_dict):
    if not style_dict:
        return "Alignment=2,OutlineColour=&H100000000,BorderStyle=1,Outline=2,Shadow=0,Fontsize=22,PrimaryColour=&H00FFFFFF,Bold=-1,MarginV=60"
        
    font_size = style_dict.get('fontSize', 24)
    color = hex_to_ass_color(style_dict.get('color', '#FFFFFF'))
    outline = style_dict.get('outline', 2)
    shadow = style_dict.get('shadow', 0)
    position = style_dict.get('position', 'bottom')
    
    alignment = 2 if position == 'bottom' else 5 # 5 is center center
    margin_v = 60 if position == 'bottom' else 0
    
    return f"Alignment={alignment},OutlineColour=&H100000000,BorderStyle=1,Outline={outline},Shadow={shadow},Fontsize={font_size},PrimaryColour={color},Bold=-1,MarginV={margin_v}"

async def burn_captions_async(video_path, captions, caption_style, output_dir):
    temp_id = str(uuid.uuid4())
    srt_filename = f"{temp_id}.srt"
    srt_filepath = os.path.join(output_dir, srt_filename)
    
    output_filename = f"{temp_id}_captioned.mp4"
    output_filepath = os.path.join(output_dir, output_filename)
    
    # 1. Generate SRT file
    generate_srt(captions, srt_filepath)
    
    # We must escape the path for ffmpeg filter
    escaped_srt_path = srt_filepath.replace("\\", "/").replace(":", "\\:")
    
    # Build dynamic style
    style = build_ass_style(caption_style)
    
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
