import google.generativeai as genai
import os
import httpx
import uuid
import boto3
from botocore.config import Config
from PIL import Image
import io

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET", "animai-videos")
R2_PUBLIC_BASE = "https://pub-410f3488491a42f5a631e8944960bd55.r2.dev"

genai.configure(api_key=GEMINI_API_KEY)


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


async def generate_character_image(character_prompt: str) -> str:
    """Adım 1: Beyaz bg'da karakter PNG üret, R2'ye yükle, URL dön."""
    model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")

    response = model.generate_content(
        character_prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="image/png"
        )
    )

    image_bytes = response.candidates[0].content.parts[0].inline_data.data
    url = upload_to_r2(image_bytes, "characters")
    return url


async def generate_scene_image(scene_prompt: str, character_image_url: str) -> str:
    """Adım 2: Karakter PNG'yi referans alarak sahne image üret."""
    model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")

    # Karakter PNG'yi indir
    async with httpx.AsyncClient() as client:
        resp = await client.get(character_image_url, timeout=60)
        resp.raise_for_status()
        char_bytes = resp.content

    # PIL Image olarak aç
    char_image = Image.open(io.BytesIO(char_bytes))

    response = model.generate_content(
        [scene_prompt, char_image],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="image/png"
        )
    )

    image_bytes = response.candidates[0].content.parts[0].inline_data.data
    url = upload_to_r2(image_bytes, "scenes")
    return url
