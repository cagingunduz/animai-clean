import replicate
import httpx
import os

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
REMOVEBG_API_KEY = os.environ.get("REMOVEBG_API_KEY")

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
    """Remove background using remove.bg API, upload result to Replicate files API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.remove.bg/v1.0/removebg",
            headers={"X-Api-Key": REMOVEBG_API_KEY},
            data={"image_url": image_url, "size": "auto"},
            timeout=60,
        )
        resp.raise_for_status()
        png_bytes = resp.content

    # Upload to Replicate files API — returns a public URL usable by other Replicate models
    async with httpx.AsyncClient() as client:
        upload_resp = await client.post(
            "https://api.replicate.com/v1/files",
            headers={
                "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
                "Content-Type": "image/png",
            },
            content=png_bytes,
            timeout=60,
        )
        upload_resp.raise_for_status()
        return upload_resp.json()["urls"]["get"]

async def animate_character(image_url: str) -> str:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "kwaivgi/kling-v2.1",
        input={
            "start_image": image_url,
            "prompt": "character talking, subtle body movement, blinking eyes, slight head movement",
            "duration": 5,
            "cfg_scale": 0.5
        }
    )
    return _extract_url(output)

async def lip_sync(video_url: str, audio_url: str) -> str:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "latentlabs/latentsync",
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
