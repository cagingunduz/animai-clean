import boto3
import os
from botocore.config import Config

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET", "animai-videos")

def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

async def upload_video(file_path: str, job_id: str) -> str:
    """Upload video to R2 and return public URL"""
    client = get_r2_client()
    key = f"videos/{job_id}.mp4"
    
    with open(file_path, "rb") as f:
        client.upload_fileobj(
            f, 
            R2_BUCKET, 
            key,
            ExtraArgs={"ContentType": "video/mp4"}
        )
    
    # Public URL — R2 bucket'ın public olması lazım
    return f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{key}"
