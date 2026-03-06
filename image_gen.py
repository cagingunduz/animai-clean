import replicate
import httpx
import os
import base64

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

async def generate_character(prompt: str) -> str:
    """Generate cartoon character PNG using Flux-1.1-pro"""
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
    # output is a URL string
    return str(output)

async def generate_background(prompt: str) -> str:
    """Generate background image using Flux-1.1-pro"""
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
    return str(output)

async def remove_background(image_url: str) -> str:
    """Remove background from character image"""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285d65c14638e5b5e9d56b1b62e",
        input={"image": image_url}
    )
    return str(output)

async def animate_character(image_url: str) -> str:
    """Animate character using Kling"""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "kwaivgi/kling-v2.1",
        input={
            "image": image_url,
            "prompt": "character talking, subtle body movement, blinking eyes, slight head movement, natural idle animation",
            "duration": 5,
            "cfg_scale": 0.5
        }
    )
    return str(output)

async def lip_sync(video_url: str, audio_url: str) -> str:
    """Apply lip sync using LatentSync"""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "bytedance/latentsync:9d5e38b1d749cee2d04ce871ede6e21c01bcebfce8f0a7b9a44b6b1fc6b1de1f",
        input={
            "video": video_url,
            "audio": audio_url
        }
    )
    return str(output)

async def download_file(url: str) -> bytes:
    """Download file from URL"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60)
        return response.content
