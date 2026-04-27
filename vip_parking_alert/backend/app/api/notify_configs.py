import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..db.session import get_db
from ..models import SpotNotifyConfig, Contact
from ..schemas.common import ApiResponse, PaginatedResponse
from ..schemas.notify_config import NotifyConfigCreate, NotifyConfigUpdate, NotifyConfigResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["通知配置管理"])


@router.get(
    "/api/spots/{spot_id}/notify-configs",
    response_model=PaginatedResponse[NotifyConfigResponse],
)
def list_notify_configs(
    spot_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取某车位所有通知配置（join contacts获取contact_name）"""
    query = db.query(SpotNotifyConfig).filter(SpotNotifyConfig.spot_id == spot_id)

    total = query.count()
    items = (
        query.options(joinedload(SpotNotifyConfig.contact))
        .order_by(SpotNotifyConfig.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for item in items:
        data = NotifyConfigResponse.model_validate(item).model_dump()
        if item.contact:
            data["contact_name"] = item.contact.name
        else:
            data["contact_name"] = None
        results.append(data)

    logger.info(f"查询车位通知配置: spot_id={spot_id}, total={total}")
    return PaginatedResponse(
        data=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/api/spots/{spot_id}/notify-configs",
    response_model=ApiResponse[NotifyConfigResponse],
)
def create_notify_config(
    spot_id: int,
    body: NotifyConfigCreate,
    db: Session = Depends(get_db),
):
    """新增通知配置"""
    config = SpotNotifyConfig(
        spot_id=spot_id,
        notify_type=body.notify_type,
        target=body.target,
        contact_id=body.contact_id,
        enabled=body.enabled,
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    result = NotifyConfigResponse.model_validate(config).model_dump()
    if config.contact_id:
        contact = db.query(Contact).filter(Contact.id == config.contact_id).first()
        result["contact_name"] = contact.name if contact else None

    logger.info(f"新增通知配置: id={config.id}, spot_id={spot_id}")
    return ApiResponse(data=result, message="新增成功")


@router.put(
    "/api/notify-configs/{config_id}",
    response_model=ApiResponse[NotifyConfigResponse],
)
def update_notify_config(
    config_id: int,
    body: NotifyConfigUpdate,
    db: Session = Depends(get_db),
):
    """修改通知配置"""
    config = db.query(SpotNotifyConfig).filter(SpotNotifyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="通知配置不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)

    result = NotifyConfigResponse.model_validate(config).model_dump()
    if config.contact_id:
        contact = db.query(Contact).filter(Contact.id == config.contact_id).first()
        result["contact_name"] = contact.name if contact else None

    logger.info(f"修改通知配置: id={config_id}")
    return ApiResponse(data=result, message="修改成功")


@router.delete("/api/notify-configs/{config_id}", response_model=ApiResponse)
def delete_notify_config(
    config_id: int,
    db: Session = Depends(get_db),
):
    """删除通知配置"""
    config = db.query(SpotNotifyConfig).filter(SpotNotifyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="通知配置不存在")

    db.delete(config)
    db.commit()

    logger.info(f"删除通知配置: id={config_id}")
    return ApiResponse(message="删除成功")
