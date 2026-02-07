from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from app.database import Base
from datetime import datetime

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    workflow_name = Column(String)
    workflow_id = Column(Integer)
    run_id = Column(Integer, unique=True, index=True)
    status = Column(String)  # completed, in_progress, queued
    conclusion = Column(String)  # success, failure, cancelled
    run_number = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    run_started_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<WorkflowRun {self.repo_name}/{self.workflow_name} - {self.conclusion}>"