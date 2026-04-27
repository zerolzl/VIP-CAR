import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models import Contact
from ..schemas.common import ApiResponse, PaginatedResponse
from ..schemas.contact import ContactCreate, ContactUpdate, ContactResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contacts", tags=["通讯录管理"])


@router.get("", response_model=PaginatedResponse[ContactResponse])
def list_contacts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词(name/phone)"),
    db: Session = Depends(get_db),
):
    """获取通讯录列表，支持分页和关键词搜索"""
    query = db.query(Contact)

    if search:
        keyword = f"%{search}%"
        query = query.filter(
            or_(
                Contact.name.like(keyword),
                Contact.phone.like(keyword),
            )
        )

    total = query.count()
    items = query.order_by(Contact.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    results = [ContactResponse.model_validate(item) for item in items]

    logger.info(f"查询通讯录列表: page={page}, page_size={page_size}, total={total}")
    return PaginatedResponse(
        data=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[ContactResponse])
def create_contact(
    body: ContactCreate,
    db: Session = Depends(get_db),
):
    """新增联系人"""
    contact = Contact(
        name=body.name,
        phone=body.phone,
        enabled=body.enabled,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)

    logger.info(f"新增联系人: id={contact.id}, name={contact.name}")
    return ApiResponse(data=ContactResponse.model_validate(contact), message="新增成功")


@router.put("/{contact_id}", response_model=ApiResponse[ContactResponse])
def update_contact(
    contact_id: int,
    body: ContactUpdate,
    db: Session = Depends(get_db),
):
    """编辑联系人"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)

    logger.info(f"编辑联系人: id={contact.id}, name={contact.name}")
    return ApiResponse(data=ContactResponse.model_validate(contact), message="编辑成功")


@router.delete("/{contact_id}", response_model=ApiResponse)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    """删除联系人"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    db.delete(contact)
    db.commit()

    logger.info(f"删除联系人: id={contact_id}")
    return ApiResponse(message="删除成功")
