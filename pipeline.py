import os
import tempfile
from jobs import job_store
from prompt_generator import generate_character_prompt, generate_background_prompt
from image_gen import generate_character, generate_background, remove_background, animate_character, lip_sync
from tts import generate_speech
from compositor import compose_video
from storage import upload_video

def update_job(job_id: str, status: str, step: str, video_url: str = "", error: str = ""):
    job_store[job_id] = {
        "status": status,
        "step": step,
        "video_url": video_url,
        "error": error
    }

async def run_pipeline(job_id: str, scene: str, dialogue: str, voice_id: str):
    try:
        # Step 1 — Generate prompts
        update_job(job_id, "processing", "Step 1: Generating prompts...")
        char_prompt = await generate_character_prompt(scene)
        bg_prompt = await generate_background_prompt(scene)

        # Step 2 — Generate character image
        update_job(job_id, "processing", "Step 2: Creating character...")
        char_url = await generate_character(char_prompt)

        # Step 3 — Generate background
        update_job(job_id, "processing", "Step 3: Creating background...")
        bg_url = await generate_background(bg_prompt)

        # Step 4 — Remove background from character
        update_job(job_id, "processing", "Step 4: Removing background...")
        char_nobg_url = await remove_background(char_url)

        # Step 5 — Generate speech
        update_job(job_id, "processing", "Step 5: Generating voice...")
        audio_bytes = await generate_speech(dialogue, voice_id)

        # Step 6 — Animate character
        update_job(job_id, "processing", "Step 6: Animating character...")
        animated_url = await animate_character(char_nobg_url)

        # Step 7 — Lip sync
        update_job(job_id, "processing", "Step 7: Applying lip sync...")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            audio_path = f.name

        audio_url = await upload_video(audio_path, f"{job_id}_audio")
        os.unlink(audio_path)

        lipsync_url = await lip_sync(animated_url, audio_url)

        # Step 8 — Compose final video
        update_job(job_id, "processing", "Step 8: Composing final video...")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        audio_bytes = await generate_speech(dialogue, voice_id)
        await compose_video(char_nobg_url, bg_url, lipsync_url, audio_bytes, output_path)

        # Step 9 — Upload to R2
        update_job(job_id, "processing", "Step 9: Uploading video...")
        video_url = await upload_video(output_path, job_id)
        os.unlink(output_path)

        update_job(job_id, "completed", "Done!", video_url=video_url)

    except Exception as e:
        update_job(job_id, "failed", "❌ Error", error=str(e))
        raise
