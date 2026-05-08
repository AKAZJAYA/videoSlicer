from fastapi import APIRouter, Request
from pydantic import BaseModel
import os
from app.controllers.image_controller import generate_image_controller

router = APIRouter()

class GenerateImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"

@router.post("/api/generate-image")
async def generate_image(request_body: GenerateImageRequest, request: Request):
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
    return await generate_image_controller(request_body.prompt, request_body.aspect_ratio, request, static_dir)
