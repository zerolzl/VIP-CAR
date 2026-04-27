"""APScheduler定时任务定义"""
import logging
from ..services.patrol_service import PatrolService

logger = logging.getLogger(__name__)

def patrol_job():
    """APScheduler定时触发的巡检任务"""
    try:
        PatrolService.execute_patrol()
    except Exception as e:
        logger.error(f"巡检任务异常: {e}", exc_info=True)
