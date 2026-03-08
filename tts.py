import httpx
import os

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"


async def generate_speech(text: str, voice_id: str) -> bytes:
    """ElevenLabs ile metni sese çevir, MP3 bytes dön."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            },
            timeout=60
        )
        response.raise_for_status()
        return response.content


async def get_voices() -> list:
    """Mevcut sesleri listele."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ELEVENLABS_API_URL}/voices",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return [
            {
                "voice_id": v["voice_id"],
                "name": v["name"],
                "category": v.get("category", ""),
                "preview_url": v.get("preview_url", "")
            }
            for v in data.get("voices", [])
        ]
