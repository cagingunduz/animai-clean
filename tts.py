import os
from elevenlabs.client import ElevenLabs


async def generate_speech(text: str, voice_id: str) -> bytes:
    client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
    
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    
    audio_bytes = b"".join(audio)
    return audio_bytes


async def get_voices() -> list:
    client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
    response = client.voices.get_all()
    return [
        {
            "voice_id": v.voice_id,
            "name": v.name,
            "category": v.category or "",
            "preview_url": v.preview_url or "",
            "labels": dict(v.labels) if v.labels else {},
        }
        for v in response.voices
    ]
