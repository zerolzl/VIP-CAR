from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    spot_id: int
    spot_number: Optional[str] = None
    plate_number: str
    sent_via: str
    sent_time: datetime
    is_resolved: int
    resolved_time: Optional[datetime]
    result: Optional[str]

    class Config:
        from_attributes = True

class AlertQuery(BaseModel):
    spot_id: Optional[int] = None
    plate_number: Optional[str] = None
    is_resolved: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
