from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SpotCreate(BaseModel):
    spot_number: str = Field(..., max_length=20, description="车位编号")
    owner: Optional[str] = Field(None, max_length=50, description="所属人")
    allowed_plates: list[str] = Field(..., description="允许车牌列表")
    status: int = Field(1, description="1启用 0停用")

class SpotUpdate(BaseModel):
    spot_number: Optional[str] = Field(None, max_length=20)
    owner: Optional[str] = Field(None, max_length=50)
    allowed_plates: Optional[list[str]] = None
    status: Optional[int] = None
    monitoring: Optional[bool] = None

class SpotResponse(BaseModel):
    id: int
    spot_number: str
    owner: Optional[str]
    allowed_plates: list[str]
    status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
