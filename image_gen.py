import os
import httpx
import uuid
import io
import base64
import boto3
import replicate
from botocore.config import Config

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET", "animai-videos")
R2_PUBLIC_BASE = "https://pub-410f3488491a42f5a631e8944960bd55.r2.dev"


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )


def upload_to_r2(image_bytes: bytes, folder: str, content_type: str = "image/png") -> str:
    s3 = get_r2_client()
    key = f"{folder}/{uuid.uuid4()}.png"
    s3.put_object(Bucket=R2_BUCKET, Key=key, Body=image_bytes, ContentType=content_type)
    return f"{R2_PUBLIC_BASE}/{key}"


def _extract_url(output) -> str:
    if output is None:
        raise ValueError("Replicate returned None output")
    if isinstance(output, list):
        output = output[0]
    if hasattr(output, 'url'):
        return str(output.url)
    return str(output)


async def generate_character_image(character_prompt: str) -> str:
    """Adim 2: Beyaz bg'da karakter PNG uret, R2'ye yukle, URL don."""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    output = client.run(
        "google/gemini-2.5-flash-image",
        input={
            "prompt": character_prompt,
            "aspect_ratio": "1:1",
            "output_format": "png"
        }
    )

    image_url = _extract_url(output)

    async with httpx.AsyncClient() as http:
        resp = await http.get(image_url, timeout=60)
        resp.raise_for_status()
        image_bytes = resp.content

    return upload_to_r2(image_bytes, "characters")


async def generate_scene_image(scene_prompt: str, character_image_url: str) -> str:
    """Adim 3: Karakter PNG'yi referans alarak sahne image uret."""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    output = client.run(
        "google/gemini-2.5-flash-image",
        input={
            "prompt": scene_prompt,
            "image": character_image_url,
            "aspect_ratio": "16:9",
            "output_format": "png"
        }
    )

    image_url = _extract_url(output)

    async with httpx.AsyncClient() as http:
        resp = await http.get(image_url, timeout=60)
        resp.raise_for_status()
        image_bytes = resp.content

    return upload_to_r2(image_bytes, "scenes")
