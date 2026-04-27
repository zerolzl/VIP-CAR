from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NotifyConfigCreate(BaseModel):
    notify_type: str = Field(..., description="sms或webhook")
    target: str = Field(..., max_length=255, description="手机号或Webhook URL")
    contact_id: Optional[int] = Field(None, description="关联联系人ID")
    enabled: int = Field(1, description="1启用 0停用")

class NotifyConfigUpdate(BaseModel):
    notify_type: Optional[str] = None
    target: Optional[str] = Field(None, max_length=255)
    contact_id: Optional[int] = None
    enabled: Optional[int] = None

class NotifyConfigResponse(BaseModel):
    id: int
    spot_id: int
    notify_type: str
    target: str
    contact_id: Optional[int]
    enabled: int
    created_at: datetime
    updated_at: datetime
    contact_name: Optional[str] = None

    class Config:
        from_attributes = True
