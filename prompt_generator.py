import anthropic
import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def generate_scene_prompt(
    user_scene: str,
    character_description: str,
    aspect_ratio: str,
    character_framing: str
) -> dict:
    """
    Kullanıcının kısa sahne açıklamasını Gemini için detaylı prompta çevirir.
    character_prompt: beyaz bg'da karakter için
    scene_prompt: karakterin sahnede olduğu kompozisyon için
    """

    framing_map = {
        "full_body": "full body shot, character visible from head to toe",
        "half_body": "half body shot, character visible from waist up",
        "close_up": "close-up shot, face and upper chest"
    }

    ratio_map = {
        "16:9": "wide horizontal composition, 16:9 aspect ratio",
        "9:16": "vertical composition, 9:16 aspect ratio, suitable for mobile/shorts",
        "1:1": "square composition, 1:1 aspect ratio"
    }

    framing_text = framing_map.get(character_framing, framing_map["full_body"])
    ratio_text = ratio_map.get(aspect_ratio, ratio_map["16:9"])

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""You are an expert prompt engineer for AI image generation.
Generate two prompts for a 2D western cartoon animation scene.

User's scene description: {user_scene}
Character description: {character_description}
Aspect ratio: {ratio_text}
Character framing: {framing_text}

Generate:
1. CHARACTER_PROMPT: For generating the character alone on a clean white background. Full detail about appearance, outfit, expression. Archer FX cartoon style.
2. SCENE_PROMPT: For placing the SAME character in the described scene/environment. Must reference the character's exact appearance for consistency.

Both prompts must include: "2D western cartoon illustration, bold thick black outlines, flat cel-shaded colors, limited color palette, clean vector-like art style, inspired by Archer FX animated series, no photorealism, no 3D, no blur, high quality digital illustration"

Respond in this exact format:
CHARACTER_PROMPT: [prompt here]
SCENE_PROMPT: [prompt here]"""
            }
        ]
    )

    text = message.content[0].text
    lines = text.strip().split("\n")

    character_prompt = ""
    scene_prompt = ""

    for line in lines:
        if line.startswith("CHARACTER_PROMPT:"):
            character_prompt = line.replace("CHARACTER_PROMPT:", "").strip()
        elif line.startswith("SCENE_PROMPT:"):
            scene_prompt = line.replace("SCENE_PROMPT:", "").strip()

    return {
        "character_prompt": character_prompt,
        "scene_prompt": scene_prompt
    }
