import os
import uuid
import asyncio
import urllib.parse
import urllib.request

def download_image_sync(prompt: str, aspect_ratio: str, output_dir: str) -> str:
    """
    Downloads an AI generated image from pollinations.ai using a prompt and an aspect ratio.
    """
    # Map aspect ratios to typical dimensions
    dimensions = {
        '1:1': (1024, 1024),
        '16:9': (1024, 576),
        '9:16': (576, 1024),
        '4:5': (800, 1000),
        '3:2': (1024, 683)
    }

    width, height = dimensions.get(aspect_ratio, (1024, 1024))

    encoded_prompt = urllib.parse.quote(prompt)
    base_provider_url = os.getenv("IMAGE_PROVIDER_URL", "https://image.pollinations.ai")
    url = f"{base_provider_url}/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"

    temp_id = str(uuid.uuid4())
    filename = f"{temp_id}_image.jpg"
    filepath = os.path.join(output_dir, filename)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            data = response.read()
            out_file.write(data)

        return filename
    except Exception as e:
        raise Exception(f"Failed to generate image: {str(e)}")

async def generate_image_async(prompt: str, aspect_ratio: str, output_dir: str) -> str:
    """
    Asynchronously delegates the image downloading blocking call to an executor.
    """
    loop = asyncio.get_event_loop()
    filename = await loop.run_in_executor(None, download_image_sync, prompt, aspect_ratio, output_dir)
    return filename
