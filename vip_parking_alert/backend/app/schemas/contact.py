from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ContactCreate(BaseModel):
    name: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)
    enabled: int = Field(1, description="1启用 0停用")

class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    enabled: Optional[int] = None

class ContactResponse(BaseModel):
    id: int
    name: str
    phone: str
    enabled: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
