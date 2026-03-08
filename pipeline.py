import traceback
from jobs import job_store
from prompt_generator import generate_scene_prompt
from image_gen import generate_character_image, generate_scene_image
from video_gen import animate_scene
from tts import generate_speech
from lipsync import apply_lipsync
from storage import upload_final_video


def log(job_id: str, step: int, total: int, message: str, status: str = "processing"):
    job_store[job_id]["status"] = status
    job_store[job_id]["step"] = step
    job_store[job_id]["total_steps"] = total
    job_store[job_id]["message"] = message
    print(f"[{job_id}] Step {step}/{total}: {message}")


async def run_pipeline(job_id: str, payload: dict):
    TOTAL = 7
    try:
        scene_text        = payload["scene_text"]
        character_desc    = payload["character_description"]
        dialogue          = payload["dialogue"]
        voice_id          = payload["voice_id"]
        aspect_ratio      = payload.get("aspect_ratio", "16:9")
        character_framing = payload.get("character_framing", "full_body")

        # ADIM 1 — Prompt üretimi (Claude)
        log(job_id, 1, TOTAL, "Sahne ve karakter promptları oluşturuluyor...")
        prompts = await generate_scene_prompt(
            user_scene=scene_text,
            character_description=character_desc,
            aspect_ratio=aspect_ratio,
            character_framing=character_framing
        )
        character_prompt = prompts["character_prompt"]
        scene_prompt     = prompts["scene_prompt"]

        # ADIM 2 — Karakter PNG (Gemini)
        log(job_id, 2, TOTAL, "Karakter görseli üretiliyor (Gemini)...")
        character_url = await generate_character_image(character_prompt)

        # ADIM 3 — Sahne PNG (Gemini, karakter referanslı)
        log(job_id, 3, TOTAL, "Sahne görseli üretiliyor (Gemini)...")
        scene_url = await generate_scene_image(scene_prompt, character_url)

        # ADIM 4 — Sessiz animasyon (Seedance)
        log(job_id, 4, TOTAL, "Animasyon üretiliyor (Seedance)...")
        silent_video_url = await animate_scene(scene_url, scene_text)

        # ADIM 5 — Ses üretimi (ElevenLabs)
        log(job_id, 5, TOTAL, "Ses üretiliyor (ElevenLabs)...")
        audio_bytes = await generate_speech(dialogue, voice_id)

        # ADIM 6 — Lip Sync
        log(job_id, 6, TOTAL, "Lip sync uygulanıyor...")
        lipsynced_url = await apply_lipsync(silent_video_url, audio_bytes)

        # ADIM 7 — R2'ye yükle
        log(job_id, 7, TOTAL, "Video yükleniyor...")
        final_url = await upload_final_video(lipsynced_url)

        job_store[job_id]["status"]      = "completed"
        job_store[job_id]["step"]        = 7
        job_store[job_id]["message"]     = "Tamamlandı!"
        job_store[job_id]["video_url"]   = final_url
        job_store[job_id]["character_url"] = character_url
        job_store[job_id]["scene_url"]   = scene_url
        print(f"[{job_id}] ✅ Pipeline tamamlandı: {final_url}")

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[{job_id}] ❌ Pipeline hatası: {repr(e)}\n{tb}")
        job_store[job_id]["status"]  = "failed"
        job_store[job_id]["error"]   = repr(e)
        job_store[job_id]["traceback"] = tb
