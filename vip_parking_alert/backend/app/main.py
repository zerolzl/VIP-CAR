import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .config import get_settings
from .utils.logging_config import setup_logging
from .api.router import api_router
from .scheduler.setup import scheduler_lifespan

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info("VIP车位告警系统启动中...")
    # 启动调度器
    async with scheduler_lifespan(app):
        yield
    logger.info("VIP车位告警系统已关闭")


app = FastAPI(
    title="VIP车位告警系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册API路由
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {request.url} - {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})
