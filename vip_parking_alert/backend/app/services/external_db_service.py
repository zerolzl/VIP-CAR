"""查询SQL Server外部数据库获取车位当前停放车牌"""
import logging
from sqlalchemy import text
from ..db.external_engine import external_engine_manager
from ..db.session import SessionLocal
from ..models.external_db import ExternalDbConfig
from ..config import get_settings
from ..utils.crypto import CryptoUtil

logger = logging.getLogger(__name__)

DEFAULT_SQL_TEMPLATE = "SELECT CAR_NO FROM dbo.REG_RECORD WHERE CAM_LOCATION = '{spot_number}'"

def get_external_db_config() -> ExternalDbConfig | None:
    """从数据库获取启用的外部数据库配置"""
    db = SessionLocal()
    try:
        return db.query(ExternalDbConfig).filter(ExternalDbConfig.enabled == 1).first()
    finally:
        db.close()

def query_current_plate(spot_number: str) -> str | None:
    """
    查询指定车位的当前停放车牌。
    返回车牌号字符串，若无结果返回None。
    """
    settings = get_settings()
    db_config = get_external_db_config()
    if not db_config:
        logger.error("未找到启用的外部数据库配置")
        return None

    try:
        password = CryptoUtil.decrypt(db_config.password, settings.SECRET_KEY)
    except Exception as e:
        logger.error(f"解密外部数据库密码失败: {e}")
        return None

    try:
        engine = external_engine_manager.get_engine(
            host=db_config.host,
            port=db_config.port,
            database_name=db_config.database_name,
            username=db_config.username,
            password=password,
            db_type=db_config.db_type,
        )
        sql = DEFAULT_SQL_TEMPLATE.replace("{spot_number}", spot_number)
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            row = result.fetchone()
            if row:
                plate = row[0].strip() if row[0] else None
                return plate if plate else None
            return None
    except Exception as e:
        logger.error(f"查询SQL Server失败, 车位={spot_number}, 错误={e}")
        return None
