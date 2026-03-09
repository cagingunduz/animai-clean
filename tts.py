import os


def get_client():
    from elevenlabs.client import ElevenLabs
    return ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))


async def generate_speech(text: str, voice_id: str) -> bytes:
    client = get_client()
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    return b"".join(audio)


async def get_voices() -> list:
    client = get_client()
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
