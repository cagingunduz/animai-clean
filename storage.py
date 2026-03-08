import boto3
import httpx
import os
import uuid
from botocore.config import Config

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


async def upload_final_video(video_url: str) -> str:
    """Video URL'den dosyayı indir, R2'ye yükle, public URL dön."""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(video_url)
        resp.raise_for_status()
        video_bytes = resp.content

    s3 = get_r2_client()
    key = f"final/{uuid.uuid4()}.mp4"
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=video_bytes,
        ContentType="video/mp4"
    )
    return f"{R2_PUBLIC_BASE}/{key}"
