import httpx
import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are a cartoon character prompt generator for an AI animation system.
Convert the user's scene description into a Flux-1.1-pro image generation prompt.

Always use this exact format:
"2D western cartoon illustration, full body character portrait, [CHARACTER_DESCRIPTION], clear expressive face with distinct features, bold thick black outlines, flat cel-shaded colors, limited color palette, clean vector-like art style, inspired by Archer FX animated series, correct human anatomy, proper body proportions, arms clearly separated from body, no photorealism, no 3D, no blur, clean white background, high quality digital illustration"

Replace [CHARACTER_DESCRIPTION] with a detailed description of the character from the user's scene.
Return ONLY the prompt, nothing else."""

async def generate_character_prompt(scene: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": scene}]
            },
            timeout=30
        )
        data = response.json()
        return data["content"][0]["text"].strip()

async def generate_background_prompt(scene: str) -> str:
    system = """You are a background scene prompt generator.
Convert the user's scene into a background image prompt for Flux-1.1-pro.

Always use this format:
"2D cartoon background illustration, [SCENE_DESCRIPTION], flat cel-shaded colors, bold outlines, western animation style, no characters, no people, high quality digital illustration"

Return ONLY the prompt, nothing else."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 200,
                "system": system,
                "messages": [{"role": "user", "content": scene}]
            },
            timeout=30
        )
        data = response.json()
        return data["content"][0]["text"].strip()
