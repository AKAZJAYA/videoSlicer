from yt_dlp import YoutubeDL
import json

ydl_opts = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False
}
with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info("ytsearch1:Inception full movie", download=False)
    print(json.dumps(info['entries'][0]['webpage_url']))
