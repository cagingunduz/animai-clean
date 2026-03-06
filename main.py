from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline import run_pipeline
from jobs import job_store
import uuid

app = FastAPI(title="AnimAI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    prompt: str
    dialogue: str
    voice_id: str = "EXAVITQu4vr4xnSDxMaL"

class JobStatus(BaseModel):
    job_id: str
    status: str
    step: str = ""
    video_url: str = ""
    error: str = ""

@app.get("/")
def root():
    return {"status": "AnimAI Backend running"}

@app.post("/generate", response_model=JobStatus)
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "status": "queued",
        "step": "Starting...",
        "video_url": "",
        "error": ""
    }
    background_tasks.add_task(run_pipeline, job_id, req.prompt, req.dialogue, req.voice_id)
    return JobStatus(job_id=job_id, status="queued", step="Starting...")

@app.get("/status/{job_id}", response_model=JobStatus)
def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(job_id=job_id, **job)
