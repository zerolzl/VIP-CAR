import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from ..db.session import get_db
from ..models import AlertLog, VipParkingSpot
from ..schemas.common import ApiResponse, PaginatedResponse
from ..schemas.alert import AlertResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["告警日志"])


@router.get("", response_model=PaginatedResponse[AlertResponse])
def list_alerts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    spot_id: Optional[int] = Query(None, description="车位ID"),
    plate_number: Optional[str] = Query(None, description="车牌号"),
    is_resolved: Optional[int] = Query(None, description="是否已解决(0未解决 1已解决)"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
):
    """查询历史告警，支持多条件筛选和分页（join vip_parking_spots获取spot_number）"""
    query = db.query(AlertLog).join(VipParkingSpot, AlertLog.spot_id == VipParkingSpot.id)

    if spot_id is not None:
        query = query.filter(AlertLog.spot_id == spot_id)

    if plate_number:
        query = query.filter(AlertLog.plate_number == plate_number)

    if is_resolved is not None:
        query = query.filter(AlertLog.is_resolved == is_resolved)

    if start_time:
        query = query.filter(AlertLog.sent_time >= start_time)

    if end_time:
        query = query.filter(AlertLog.sent_time <= end_time)

    total = query.count()
    items = (
        query.options(joinedload(AlertLog.spot))
        .order_by(AlertLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for item in items:
        data = AlertResponse.model_validate(item).model_dump()
        data["spot_number"] = item.spot.spot_number if item.spot else None
        results.append(data)

    logger.info(f"查询告警日志: page={page}, page_size={page_size}, total={total}")
    return PaginatedResponse(
        data=results,
        total=total,
        page=page,
        page_size=page_size,
    )
