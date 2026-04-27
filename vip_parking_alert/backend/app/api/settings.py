import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from ..db.session import get_db
from ..models import ExternalDbConfig, SmsGatewayConfig
from ..schemas.common import ApiResponse
from ..schemas.settings import (
    ExternalDbCreate,
    ExternalDbUpdate,
    ExternalDbResponse,
    SmsGatewayCreate,
    SmsGatewayUpdate,
    SmsGatewayResponse,
)
from ..config import get_settings
from ..utils.crypto import CryptoUtil

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["系统设置"])


# ==================== 外部数据库配置 ====================


@router.get("/external-db", response_model=ApiResponse[ExternalDbResponse])
def get_external_db(db: Session = Depends(get_db)):
    """获取外部数据库配置（密码返回掩码****）"""
    config = db.query(ExternalDbConfig).filter(ExternalDbConfig.enabled == 1).first()
    if not config:
        result = {
            "id": 0,
            "name": "",
            "db_type": "mssql",
            "host": "",
            "port": 1433,
            "database": "",
            "username": "",
            "password": "",
            "enabled": False
        }
        logger.info("外部数据库配置不存在，返回默认值")
        return ApiResponse(data=result)

    result = ExternalDbResponse.model_validate(config).model_dump()
    result["password"] = "****"
    result["database"] = result.pop("database_name", "")

    logger.info("获取外部数据库配置")
    return ApiResponse(data=result)


@router.put("/external-db", response_model=ApiResponse[ExternalDbResponse])
def update_external_db(
    body: ExternalDbUpdate,
    db: Session = Depends(get_db),
):
    """更新或创建外部数据库配置（密码若非空则加密存储，为空保留原值）"""
    config = db.query(ExternalDbConfig).filter(ExternalDbConfig.enabled == 1).first()
    settings = get_settings()
    update_data = body.model_dump()

    if "database" in update_data and update_data["database"] is not None:
        update_data["database_name"] = update_data.pop("database")
    elif "database_name" not in update_data or update_data.get("database_name") is None:
        update_data["database_name"] = update_data.get("database", "")

    if "password" in update_data:
        password = update_data.pop("password")
        if password and password != "****":
            update_data["password"] = CryptoUtil.encrypt(password, settings.SECRET_KEY)
        elif not config:
            raise HTTPException(status_code=400, detail="密码不能为空")

    if config:
        for key, value in update_data.items():
            if value is not None:
                setattr(config, key, value)
    else:
        required_fields = ["host", "port", "database_name", "username"]
        for field in required_fields:
            if not update_data.get(field):
                raise HTTPException(status_code=400, detail=f"{field} 不能为空")
        
        config = ExternalDbConfig(**update_data)
        db.add(config)

    db.commit()
    db.refresh(config)

    result = ExternalDbResponse.model_validate(config).model_dump()
    result["password"] = "****"
    result["database"] = result.get("database_name", "")

    logger.info("更新外部数据库配置")
    return ApiResponse(data=result, message="更新成功")


@router.post("/external-db/test", response_model=ApiResponse)
def test_external_db(db: Session = Depends(get_db)):
    """测试外部数据库连接（解密密码后尝试连接）"""
    config = db.query(ExternalDbConfig).filter(ExternalDbConfig.enabled == 1).first()
    if not config:
        raise HTTPException(status_code=404, detail="外部数据库配置不存在")

    settings = get_settings()

    try:
        decrypted_password = CryptoUtil.decrypt(config.password, settings.SECRET_KEY)
    except Exception as e:
        logger.error(f"解密外部数据库密码失败: {e}")
        raise HTTPException(status_code=500, detail="密码解密失败，请检查配置")

    try:
        db_type = config.db_type.lower()
        
        if db_type == "mssql":
            db_url = (
                f"mssql+pyodbc://{config.username}:{decrypted_password}"
                f"@{config.host}:{config.port}/{config.database_name}"
                f"?driver=ODBC+Driver+18+for+SQL+Server"
                f"&TrustServerCertificate=yes"
            )
        elif db_type == "mysql":
            db_url = (
                f"mysql+pymysql://{config.username}:{decrypted_password}"
                f"@{config.host}:{config.port}/{config.database_name}"
                f"?charset=utf8mb4"
            )
        elif db_type == "postgresql":
            db_url = (
                f"postgresql+psycopg2://{config.username}:{decrypted_password}"
                f"@{config.host}:{config.port}/{config.database_name}"
            )
        elif db_type == "sqlite":
            db_url = f"sqlite:///{config.database_name}"
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据库类型: {db_type}")

        test_engine = create_engine(db_url, pool_pre_ping=True)
        with test_engine.connect() as conn:
            if db_type == "mssql":
                conn.execute("SELECT 1")
            elif db_type == "mysql":
                conn.execute("SELECT 1")
            elif db_type == "postgresql":
                conn.execute("SELECT 1")
            elif db_type == "sqlite":
                conn.execute("SELECT 1")
        test_engine.dispose()

        logger.info("外部数据库连接测试成功")
        return ApiResponse(message="连接成功")
    except Exception as e:
        logger.error(f"外部数据库连接测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


# ==================== 短信网关配置 ====================


@router.get("/sms-gateway", response_model=ApiResponse[SmsGatewayResponse])
def get_sms_gateway(db: Session = Depends(get_db)):
    """获取短信网关配置（token返回掩码****）"""
    config = db.query(SmsGatewayConfig).filter(SmsGatewayConfig.enabled == 1).first()
    if not config:
        result = {
            "id": 0,
            "name": "",
            "url": "",
            "token": "",
            "sender_id": "",
            "enabled": False
        }
        logger.info("短信网关配置不存在，返回默认值")
        return ApiResponse(data=result)

    result = SmsGatewayResponse.model_validate(config).model_dump()
    result["token"] = "****"
    result["sender_id"] = result.get("sender_id", result.get("from_param", ""))

    logger.info("获取短信网关配置")
    return ApiResponse(data=result)


@router.put("/sms-gateway", response_model=ApiResponse[SmsGatewayResponse])
def update_sms_gateway(
    body: SmsGatewayUpdate,
    db: Session = Depends(get_db),
):
    """更新或创建短信网关配置（token若非空则原样存储，为空保留原值）"""
    config = db.query(SmsGatewayConfig).filter(SmsGatewayConfig.enabled == 1).first()
    update_data = body.model_dump(exclude_unset=True)

    if "sender_id" in update_data:
        update_data["from_param"] = update_data.pop("sender_id")

    if "token" in update_data:
        token = update_data.pop("token")
        if token and token != "****":
            update_data["token"] = token

    if config:
        for key, value in update_data.items():
            setattr(config, key, value)
    else:
        config = SmsGatewayConfig(**update_data)
        db.add(config)

    db.commit()
    db.refresh(config)

    result = SmsGatewayResponse.model_validate(config).model_dump()
    result["token"] = "****"
    result["sender_id"] = result.get("sender_id", result.get("from_param", ""))

    logger.info("更新短信网关配置")
    return ApiResponse(data=result, message="更新成功")
