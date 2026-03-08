import replicate
import os

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")


def _extract_url(output) -> str:
    if output is None:
        raise ValueError("Replicate returned None output")
    if isinstance(output, list):
        output = output[0]
    if hasattr(output, 'url'):
        return str(output.url)
    return str(output)


async def animate_scene(scene_image_url: str, scene_description: str, duration: int = 5) -> str:
    """Adım 3: Sahne PNG'den Seedance ile sessiz animasyon üret."""
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    output = client.run(
        "bytedance/seedance-1-lite",
        input={
            "image": scene_image_url,
            "prompt": f"2D cartoon animation, {scene_description}, smooth motion, characters talking and gesturing naturally",
            "duration": duration,
            "resolution": "720p",
            "aspect_ratio": "16:9"
        }
    )
    return _extract_url(output)
