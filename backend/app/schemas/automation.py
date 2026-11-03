"""
Pydantic Schemas: AutomationLog
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.automation import AutomationStatus


class AutomationLogCreate(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=100, description="Scheduled task or background job identifier")
    status: AutomationStatus = Field(default=AutomationStatus.RUNNING, description="Current execution state")
    message: str = Field(..., description="Log summary or error details")
    started_at: datetime = Field(..., description="Job execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp, if finished")


class AutomationLogUpdate(BaseModel):
    status: Optional[AutomationStatus] = None
    message: Optional[str] = None
    completed_at: Optional[datetime] = None


class AutomationLogResponse(BaseModel):
    id: int
    task_name: str
    status: str
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
