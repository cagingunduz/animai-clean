import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from jobs import job_store
from pipeline import run_pipeline
from tts import get_voices

app = FastAPI(title="AnimAI API v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    scene_text: str                          # "Bir dedektif ofisinde dosya inceliyor"
    character_description: str               # "40 yaşında erkek dedektif, kahverengi trençkot"
    dialogue: str                            # Karakter ne söyleyecek
    voice_id: str                            # ElevenLabs voice ID
    aspect_ratio: Optional[str] = "16:9"    # "16:9" | "9:16" | "1:1"
    character_framing: Optional[str] = "full_body"  # "full_body" | "half_body" | "close_up"


@app.get("/")
async def root():
    return {"status": "AnimAI v2 online", "pipeline": "Claude → Gemini → Gemini → Seedance → ElevenLabs → LipSync"}


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
        raise HTTPException(status_code=404, detail="Job bulunamadı")
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
