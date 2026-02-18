import os
import uuid
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

from db import get_db_session, init_db
from models import Job, Output, JobStatus, JobType
from services.generators import generate_lead_list, generate_prompt_pack, generate_weekly_pilot_memo, generate_research_brief
from services.llm import generate, LLMError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan handler to replace deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (if needed)

# Initialize FastAPI app
app = FastAPI(title="Agent Ops Backend", version="1.0.0", lifespan=lifespan)

# CORS setup
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Authentication
security = HTTPBearer()
API_KEY = os.getenv("AGENT_OPS_API_KEY", "dev-key-12345")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# Pydantic models
class CreateJobRequest(BaseModel):
    type: JobType
    params: Dict[str, Any]

class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    params_json: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_text: Optional[str]

class OutputResponse(BaseModel):
    id: int
    job_id: str
    type: str
    content_text: str
    content_type: str
    created_at: datetime

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str


# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Job execution function
async def execute_job(job_id: str, job_type: JobType, params: Dict[str, Any]):
    """Execute job in background and update status"""
    db = next(get_db_session())
    
    try:
        # Update job to running
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Generate content based on job type
        if job_type == JobType.LEAD_LIST:
            content = generate_lead_list(params)  # DEPRECATED - returns notice
        elif job_type == JobType.PROMPT_PACK:
            content = generate_prompt_pack(params)
        elif job_type == JobType.WEEKLY_PILOT_MEMO:
            content = await generate_weekly_pilot_memo(params)
        elif job_type == JobType.RESEARCH_BRIEF:
            content = generate_research_brief(params)
        else:
            raise ValueError(f"Unknown job type: {job_type}")
        
        # Store output
        output = Output(
            job_id=job_id,
            type=job_type.value,
            content_text=content,
            content_type="text/markdown"
        )
        db.add(output)
        
        # Update job to succeeded
        job.status = JobStatus.SUCCEEDED.value
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        
    except Exception as e:
        # Update job to failed
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED.value
            job.error_text = str(e)
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
        logger.error(f"Job {job_id} failed: {str(e)}")
    
    finally:
        db.close()

# Create job endpoint
@app.post("/jobs", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
async def create_job(request: CreateJobRequest):
    db = next(get_db_session())
    
    try:
        # Create job record
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            type=request.type.value,
            status=JobStatus.QUEUED.value,
            params_json=json.dumps(request.params)
        )
        db.add(job)
        db.commit()
        
        # Execute job in background
        asyncio.create_task(execute_job(job_id, request.type, request.params))
        
        # Return job response
        return JobResponse(
            id=job.id,
            type=job.type,
            status=job.status,
            params_json=job.params_json,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_text=job.error_text
        )
    
    finally:
        db.close()

# Get all jobs endpoint
@app.get("/jobs", response_model=List[JobResponse], dependencies=[Depends(verify_api_key)])
async def get_jobs():
    db = next(get_db_session())
    
    try:
        jobs = db.query(Job).order_by(Job.created_at.desc()).all()
        return [
            JobResponse(
                id=job.id,
                type=job.type,
                status=job.status,
                params_json=job.params_json,
                created_at=job.created_at,
                updated_at=job.updated_at,
                started_at=job.started_at,
                finished_at=job.finished_at,
                error_text=job.error_text
            ) for job in jobs
        ]
    
    finally:
        db.close()

# Get specific job endpoint
@app.get("/jobs/{job_id}", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
async def get_job(job_id: str):
    db = next(get_db_session())
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(
            id=job.id,
            type=job.type,
            status=job.status,
            params_json=job.params_json,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_text=job.error_text
        )
    
    finally:
        db.close()

# Get job output endpoint
@app.get("/jobs/{job_id}/output", response_model=OutputResponse, dependencies=[Depends(verify_api_key)])
async def get_job_output(job_id: str):
    db = next(get_db_session())
    
    try:
        output = db.query(Output).filter(Output.job_id == job_id).first()
        if not output:
            raise HTTPException(status_code=404, detail="Output not found")
        
        return OutputResponse(
            id=output.id,
            job_id=output.job_id,
            type=output.type,
            content_text=output.content_text,
            content_type=output.content_type,
            created_at=output.created_at
        )
    
    finally:
        db.close()

# Get latest output by type endpoint
@app.get("/outputs/latest", response_model=OutputResponse, dependencies=[Depends(verify_api_key)])
async def get_latest_output(type: str):
    db = next(get_db_session())
    
    try:
        output = db.query(Output).filter(Output.type == type).order_by(Output.created_at.desc()).first()
        if not output:
            raise HTTPException(status_code=404, detail="Output not found")
        
        return OutputResponse(
            id=output.id,
            job_id=output.job_id,
            type=output.type,
            content_text=output.content_text,
            content_type=output.content_type,
            created_at=output.created_at
        )
    
    finally:
        db.close()

# Chat with job output endpoint
@app.post("/jobs/{job_id}/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat_with_job(job_id: str, request: ChatRequest):
    db = next(get_db_session())
    
    try:
        # Get the job and its output
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        output = db.query(Output).filter(Output.job_id == job_id).first()
        if not output:
            raise HTTPException(status_code=404, detail="Job output not found")
        
        # Build context from original job and output
        job_params = json.loads(job.params_json)
        
        system_prompt = f"""You are continuing a conversation about a {job.type} that was previously generated. 
        
The user is asking a follow-up question about this output. Provide a helpful response based on the context.

Original Job Type: {job.type}
Original Parameters: {json.dumps(job_params, indent=2)}
Generated Output: {output.content_text[:2000]}{'...' if len(output.content_text) > 2000 else ''}"""

        user_prompt = f"Follow-up question: {request.message}"
        
        # Generate response
        reply = generate(system_prompt, user_prompt)
        
        return ChatResponse(reply=reply)
        
    except LLMError as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))