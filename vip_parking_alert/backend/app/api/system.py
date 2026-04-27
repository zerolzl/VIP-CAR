import logging

from fastapi import APIRouter

from ..config import get_settings
from ..utils.crypto import CryptoUtil
from ..db.session import engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["系统接口"])


@router.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "version": "1.0.0"}


@router.post("/reload-config")
def reload_config():
    """热重载配置（清除Settings缓存，dispose SQL Server引擎，重置CryptoUtil）"""
    try:
        # 清除Settings的lru_cache缓存
        get_settings.cache_clear()
        logger.info("已清除Settings缓存")

        # 重置CryptoUtil的Fernet实例
        CryptoUtil.reset()
        logger.info("已重置CryptoUtil")

        # dispose数据库引擎连接池
        engine.dispose()
        logger.info("已dispose数据库引擎")

        logger.info("配置热重载完成")
        return {"status": "ok", "message": "配置重载成功"}
    except Exception as e:
        logger.error(f"配置热重载失败: {e}")
        return {"status": "error", "message": f"配置重载失败: {str(e)}"}
