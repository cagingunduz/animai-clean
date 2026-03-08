import replicate
import httpx
import os
import uuid
import boto3
from botocore.config import Config

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET", "animai-videos")
R2_PUBLIC_BASE = "https://pub-410f3488491a42f5a631e8944960bd55.r2.dev"


def _extract_url(output) -> str:
    if output is None:
        raise ValueError("Replicate returned None output")
    if isinstance(output, list):
        output = output[0]
    if hasattr(output, 'url'):
        return str(output.url)
    return str(output)


def upload_audio_to_r2(audio_bytes: bytes) -> str:
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )
    key = f"audio/{uuid.uuid4()}.mp3"
    s3.put_object(Bucket=R2_BUCKET, Key=key, Body=audio_bytes, ContentType="audio/mpeg")
    return f"{R2_PUBLIC_BASE}/{key}"


async def apply_lipsync(video_url: str, audio_bytes: bytes) -> str:
    """Adım 4b: Sessiz video + ses → lip sync'li final video."""
    # Sesi R2'ye yükle
    audio_url = upload_audio_to_r2(audio_bytes)

    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "sync/lipsync-2",
        input={
            "video": video_url,
            "audio": audio_url
        }
    )
    return _extract_url(output)
