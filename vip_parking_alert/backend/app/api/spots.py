import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models import VipParkingSpot
from ..schemas.common import ApiResponse, PaginatedResponse
from ..schemas.spot import SpotCreate, SpotUpdate, SpotResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/spots", tags=["VIP车位管理"])


def _spot_to_dict(spot: VipParkingSpot) -> dict:
    """将ORM对象转换为响应字典，解析allowed_plates JSON"""
    data = {
        "id": spot.id,
        "spot_number": spot.spot_number,
        "owner": spot.owner,
        "allowed_plates": json.loads(spot.allowed_plates) if spot.allowed_plates else [],
        "status": spot.status,
        "monitoring": spot.status == 1,
        "created_at": spot.created_at,
        "updated_at": spot.updated_at,
    }
    return data


@router.get("", response_model=PaginatedResponse[SpotResponse])
def list_spots(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词(spot_number/owner)"),
    status: Optional[int] = Query(None, description="状态过滤(1启用 0停用)"),
    monitoring: Optional[bool] = Query(None, description="监控状态过滤"),
    db: Session = Depends(get_db),
):
    """获取VIP车位列表，支持分页、关键词搜索和状态过滤"""
    query = db.query(VipParkingSpot)

    if search:
        keyword = f"%{search}%"
        query = query.filter(
            or_(
                VipParkingSpot.spot_number.like(keyword),
                VipParkingSpot.owner.like(keyword),
            )
        )

    if status is not None:
        query = query.filter(VipParkingSpot.status == status)

    if monitoring is not None:
        query = query.filter(VipParkingSpot.status == (1 if monitoring else 0))

    total = query.count()
    items = query.order_by(VipParkingSpot.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    results = [_spot_to_dict(item) for item in items]

    logger.info(f"查询VIP车位列表: page={page}, page_size={page_size}, total={total}")
    return PaginatedResponse(
        data=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[SpotResponse])
def create_spot(
    body: SpotCreate,
    db: Session = Depends(get_db),
):
    """新增VIP车位"""
    spot = VipParkingSpot(
        spot_number=body.spot_number,
        owner=body.owner,
        allowed_plates=json.dumps(body.allowed_plates, ensure_ascii=False),
        status=body.status,
    )
    db.add(spot)
    db.commit()
    db.refresh(spot)

    result = _spot_to_dict(spot)

    logger.info(f"新增VIP车位: id={spot.id}, spot_number={spot.spot_number}")
    return ApiResponse(data=result, message="新增成功")


@router.put("/{spot_id}", response_model=ApiResponse[SpotResponse])
def update_spot(
    spot_id: int,
    body: SpotUpdate,
    db: Session = Depends(get_db),
):
    """编辑VIP车位"""
    spot = db.query(VipParkingSpot).filter(VipParkingSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="车位不存在")

    update_data = body.model_dump(exclude_unset=True)
    if "allowed_plates" in update_data and update_data["allowed_plates"] is not None:
        update_data["allowed_plates"] = json.dumps(update_data["allowed_plates"], ensure_ascii=False)
    
    if "monitoring" in update_data:
        update_data["status"] = 1 if update_data["monitoring"] else 0
        del update_data["monitoring"]

    for key, value in update_data.items():
        setattr(spot, key, value)

    db.commit()
    db.refresh(spot)

    result = _spot_to_dict(spot)

    logger.info(f"编辑VIP车位: id={spot.id}, spot_number={spot.spot_number}")
    return ApiResponse(data=result, message="编辑成功")


@router.delete("/{spot_id}", response_model=ApiResponse)
def delete_spot(
    spot_id: int,
    db: Session = Depends(get_db),
):
    """删除VIP车位（级联删除通知配置）"""
    spot = db.query(VipParkingSpot).filter(VipParkingSpot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="车位不存在")

    db.delete(spot)
    db.commit()

    logger.info(f"删除VIP车位: id={spot_id}, spot_number={spot.spot_number}")
    return ApiResponse(message="删除成功")
