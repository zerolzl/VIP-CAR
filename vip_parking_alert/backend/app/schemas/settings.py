from typing import Optional
from pydantic import BaseModel, Field

class ExternalDbCreate(BaseModel):
    name: str = Field(..., max_length=50)
    db_type: str = Field("mssql", max_length=20)
    host: str = Field(..., max_length=100)
    port: int
    database_name: str = Field(..., max_length=100)
    username: str = Field(..., max_length=50)
    password: str = Field(..., description="明文密码，保存时自动加密")
    enabled: int = Field(1)

class ExternalDbUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    db_type: Optional[str] = Field(None, max_length=20)
    host: Optional[str] = Field(None, max_length=100)
    port: Optional[int] = None
    database: Optional[str] = Field(None, max_length=100)
    database_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, description="明文密码，为空则保留原值")
    enabled: Optional[int] = None

class ExternalDbResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database_name: str
    database: Optional[str] = None
    username: str
    password: str  # 返回掩码
    enabled: int

    class Config:
        from_attributes = True

class SmsGatewayCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    url: str = Field(..., max_length=255)
    token: str = Field(..., max_length=128)
    from_param: str = Field(..., max_length=50)
    enabled: int = Field(1)

class SmsGatewayUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = Field(None, max_length=255)
    token: Optional[str] = Field(None, max_length=128)
    from_param: Optional[str] = Field(None, max_length=50)
    enabled: Optional[int] = None

class SmsGatewayResponse(BaseModel):
    id: int
    name: Optional[str]
    url: str
    token: str  # 返回掩码
    from_param: str
    enabled: int

    class Config:
        from_attributes = True
