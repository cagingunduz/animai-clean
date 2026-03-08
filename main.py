import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from jobs import job_store
from pipeline import run_pipeline
from tts import get_voices, generate_speech
from lipsync import upload_audio_to_r2

app = FastAPI(title="AnimAI API v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

 
class GenerateRequest(BaseModel):
    scene_text: str
    character_description: str
    dialogue: str
    voice_id: str
    aspect_ratio: Optional[str] = "16:9"
    character_framing: Optional[str] = "full_body"


class TTSTestRequest(BaseModel):
    text: str
    voice_id: str


@app.get("/")
async def root():
    return {"status": "AnimAI v2 online", "pipeline": "Claude -> Gemini -> Gemini -> Seedance -> ElevenLabs -> LipSync"}


@app.post("/generate")
async def generate(req: GenerateRequest):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "status": "queued",
        "step": 0,
        "total_steps": 7,
        "message": "Kuyrukta bekleniyor...",
        "video_url": None,
        "character_url": None,
        "scene_url": None,
        "error": None,
        "traceback": None
    }
    asyncio.create_task(run_pipeline(job_id, req.model_dump()))
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job bulunamadi")
    job = job_store[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "step": job["step"],
        "total_steps": job["total_steps"],
        "message": job["message"],
        "video_url": job.get("video_url"),
        "character_url": job.get("character_url"),
        "scene_url": job.get("scene_url"),
        "error": job.get("error"),
        "traceback": job.get("traceback")
    }


@app.get("/voices")
async def voices():
    try:
        result = await get_voices()
        return {"voices": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts-test")
async def tts_test(req: TTSTestRequest):
    """TTS test - ses uretip R2 URL doner."""
    try:
        audio_bytes = await generate_speech(req.text, req.voice_id)
        audio_url = upload_audio_to_r2(audio_bytes)
        return {"audio_url": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))
