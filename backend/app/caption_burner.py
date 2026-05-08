import os
import uuid
import asyncio

def format_ass_time(seconds):
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    centis = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def hex_to_ass_color(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        r, g, b = hex_str[0:2], hex_str[2:4], hex_str[4:6]
        return f"&H00{b}{g}{r}"
    return "&H00FFFFFF"

def build_ass_style(style_dict):
    if not style_dict:
        return "Style: Default,Outfit,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,60,60,60,1"
        
    font_size = style_dict.get('fontSize', 24)
    color = hex_to_ass_color(style_dict.get('color', '#FFFFFF'))
    outline = style_dict.get('outline', 2)
    outline_color = hex_to_ass_color(style_dict.get('outlineColor', '#000000'))
    shadow = style_dict.get('shadow', 0)
    shadow_color = hex_to_ass_color(style_dict.get('shadowColor', '#000000'))
    position = style_dict.get('position', 'bottom')
    
    alignment = 2 if position == 'bottom' else 5 # 5 is center center
    margin_v = 60 if position == 'bottom' else 0
    
    # Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    return f"Style: Default,Outfit,{font_size},{color},&H000000FF,{outline_color},{shadow_color},-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},60,60,{margin_v},1"

def generate_ass(captions, output_filepath, caption_style, animation_style="sentence"):
    # Determine basic configuration
    position = caption_style.get('position', 'bottom') if caption_style else 'bottom'
    # Base X, Y for absolute positioning styles (glitch, slide). Assuming 720x1280 base canvas.
    base_x = 360
    base_y = 1140 if position == 'bottom' else 640

    with open(output_filepath, "w", encoding="utf-8") as f:
        # 1. Header
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 720\n")
        f.write("PlayResY: 1280\n")
        f.write("WrapStyle: 1\n\n")

        # 2. Styles
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(build_ass_style(caption_style) + "\n\n")

        # 3. Events
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        def write_dialogue(start_t, end_t, text_content):
            f.write(f"Dialogue: 0,{format_ass_time(start_t)},{format_ass_time(end_t)},Default,,0,0,0,,{text_content}\n")

        for cap in captions:
            start = float(cap["start"])
            end = float(cap["end"])
            text = cap["text"]
            has_words = "words" in cap and cap["words"]

            if animation_style == "word" and has_words:
                for w in cap["words"]:
                    write_dialogue(float(w["start"]), float(w["end"]), w["word"])
            elif animation_style == "cumulative" and has_words:
                cum_text = ""
                words = cap["words"]
                for j, w in enumerate(words):
                    ws = float(w["start"])
                    we = float(w["end"]) if j == len(words) - 1 else float(words[j+1]["start"])
                    cum_text += w["word"] + " "
                    write_dialogue(ws, we, cum_text.strip())
            elif animation_style == "karaoke" and has_words:
                # Single line, build tags
                kar_text = ""
                for w in cap["words"]:
                    dur_centis = int((float(w["end"]) - float(w["start"])) * 100)
                    kar_text += f"{{\\k{dur_centis}}}{w['word']} "
                write_dialogue(start, end, kar_text.strip())
            elif animation_style == "fade":
                write_dialogue(start, end, f"{{\\fad(250,250)}}{text}")
            elif animation_style == "popup":
                write_dialogue(start, end, f"{{\\fscx0\\fscy0\\t(0,150,\\fscx100\\fscy100)}}{text}")
            elif animation_style == "zoom":
                write_dialogue(start, end, f"{{\\fscx120\\fscy120\\t(0,150,\\fscx100\\fscy100)}}{text}")
            elif animation_style == "bounce":
                write_dialogue(start, end, f"{{\\fscx50\\fscy50\\t(0,100,\\fscx120\\fscy120)\\t(100,150,\\fscx100\\fscy100)}}{text}")
            elif animation_style == "kinetic" and has_words:
                for w in cap["words"]:
                    write_dialogue(float(w["start"]), float(w["end"]), f"{{\\fscx110\\fscy110\\t(0,100,\\fscx100\\fscy100)}}{w['word']}")
            elif animation_style == "slide":
                # Slide up
                start_y = 1300 if position == 'bottom' else 800
                write_dialogue(start, end, f"{{\\move({base_x},{start_y},{base_x},{base_y})}}{text}")
            elif animation_style == "typewriter":
                # Calculate duration per char
                total_dur = end - start
                char_count = len(text)
                if char_count == 0: continue
                char_dur = total_dur / char_count
                for i in range(1, char_count + 1):
                    sub_start = start + (i - 1) * char_dur
                    sub_end = end if i == char_count else start + i * char_dur
                    write_dialogue(sub_start, sub_end, text[:i])
            elif animation_style == "neon":
                outline_color = hex_to_ass_color(caption_style.get('outlineColor', '#FFFFFF')) if caption_style else "&H00FFFFFF"
                # Layer 1: large blur
                f.write(f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{{\\blur15\\3c{outline_color}\\alpha&H80&}}{text}\n")
                # Layer 2: medium blur
                f.write(f"Dialogue: 1,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{{\\blur8\\3c{outline_color}\\alpha&H40&}}{text}\n")
                # Layer 3: crisp text
                f.write(f"Dialogue: 2,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{text}\n")
            elif animation_style == "glitch":
                # Cyan layer shifted up-left
                f.write(f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{{\\pos({base_x-5},{base_y-5})\\c&H00FFFF&}}{text}\n")
                # Red layer shifted down-right
                f.write(f"Dialogue: 1,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{{\\pos({base_x+5},{base_y+5})\\c&H0000FF&}}{text}\n")
                # Main layer
                f.write(f"Dialogue: 2,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{{\\pos({base_x},{base_y})}}{text}\n")
            else:
                # Default "sentence"
                write_dialogue(start, end, text)


async def burn_captions_async(video_path, captions, caption_style, output_dir):
    temp_id = str(uuid.uuid4())
    ass_filename = f"{temp_id}.ass"
    ass_filepath = os.path.join(output_dir, ass_filename)
    
    output_filename = f"{temp_id}_captioned.mp4"
    output_filepath = os.path.join(output_dir, output_filename)
    
    # 1. Generate ASS file
    animation_style = caption_style.get("animationStyle", "sentence") if caption_style else "sentence"
    if captions:
        generate_ass(captions, ass_filepath, caption_style, animation_style)
    
    # We must escape the path for ffmpeg filter
    escaped_ass_path = ass_filepath.replace("\\", "/").replace(":", "\\:")
    
    if not captions:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-c:v", "copy",
            "-c:a", "copy",
            output_filepath
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"ass={escaped_ass_path}",
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
        
    # Clean up ASS
    if os.path.exists(ass_filepath):
        os.remove(ass_filepath)
        
    return output_filename
