"""APScheduler调度器初始化与生命周期管理"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ..config import get_settings
from .jobs import patrol_job

logger = logging.getLogger(__name__)

def create_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(
        timezone="Asia/Shanghai",
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        },
    )
    scheduler.add_job(
        patrol_job,
        trigger=IntervalTrigger(seconds=settings.PATROL_INTERVAL_SECONDS),
        id="vip_spot_patrol",
        name="VIP车位定时巡检",
        replace_existing=True,
    )
    return scheduler

@asynccontextmanager
async def scheduler_lifespan(app: FastAPI):
    """调度器生命周期管理"""
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("APScheduler调度器已启动")
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=True)
    logger.info("APScheduler调度器已关闭")
