import httpx
import os

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

async def generate_speech(text: str, voice_id: str) -> bytes:
    """Generate speech audio using ElevenLabs"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
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
        return response.content  # MP3 bytes
