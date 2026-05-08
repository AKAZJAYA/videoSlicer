from fastapi import Request
import os
from app.services.image_service import generate_image_async

async def generate_image_controller(prompt: str, aspect_ratio: str, request: Request, static_dir: str):
    try:
        filename = await generate_image_async(prompt, aspect_ratio, static_dir)
        # Use request.base_url to avoid hardcoding localhost
        base_url = str(request.base_url).rstrip("/")
        image_url = f"{base_url}/static/{filename}"

        return {
            "status": "success",
            "message": "Image generated successfully!",
            "image_url": image_url
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
