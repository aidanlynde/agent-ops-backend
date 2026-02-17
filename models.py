from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum
from db import Base

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class JobType(Enum):
    LEAD_LIST = "lead_list"  # DEPRECATED: kept for compatibility
    PROMPT_PACK = "prompt_pack"
    WEEKLY_PILOT_MEMO = "weekly_pilot_memo"
    RESEARCH_BRIEF = "research_brief"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=JobStatus.QUEUED.value)
    params_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error_text = Column(Text)
    
    # Relationship to outputs
    outputs = relationship("Output", back_populates="job")

class Output(Base):
    __tablename__ = "outputs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    type = Column(String, nullable=False)
    content_text = Column(Text, nullable=False)
    content_type = Column(String, nullable=False, default="text/markdown")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship to job
    job = relationship("Job", back_populates="outputs")