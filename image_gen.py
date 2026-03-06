import replicate
import httpx
import os
import io
import base64
import boto3
from PIL import Image
from rembg import remove as rembg_remove

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET", "animai-videos")

def _extract_url(output) -> str:
    """Extract plain URL string from Replicate output (FileOutput, list, or str)."""
    if output is None:
        raise ValueError("Replicate returned None output")
    if isinstance(output, list):
        output = output[0]
    # FileOutput has a .url attribute
    if hasattr(output, 'url'):
        return str(output.url)
    return str(output)

async def generate_character(prompt: str) -> str:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
            "output_format": "png"
        }
    )
    return _extract_url(output)

async def generate_background(prompt: str) -> str:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": prompt,
            "width": 1440,
            "height": 832,
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
            "output_format": "png"
        }
    )
    return _extract_url(output)

async def remove_background(image_url: str) -> str:
    """Download image, remove bg locally with rembg, upload to R2, return URL."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(image_url, timeout=60)
        resp.raise_for_status()
        img_bytes = resp.content

    # Remove background locally
    output_bytes = rembg_remove(img_bytes)

    # Upload PNG with transparency to R2
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )
    import uuid
    key = f"nobg/{uuid.uuid4()}.png"
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=output_bytes,
        ContentType="image/png",
    )
    return f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{R2_BUCKET}/{key}"

async def animate_character(image_url: str) -> str:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "kwaivgi/kling-v2.1-standard",
        input={
            "image": image_url,
            "prompt": "character talking, subtle body movement, blinking eyes, slight head movement",
            "duration": 5,
            "cfg_scale": 0.5
        }
    )
    return _extract_url(output)

async def lip_sync(video_url: str, audio_url: str) -> str:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "bytedance/latentsync",
        input={
            "video": video_url,
            "audio": audio_url
        }
    )
    return _extract_url(output)

async def download_file(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60)
        return response.content
