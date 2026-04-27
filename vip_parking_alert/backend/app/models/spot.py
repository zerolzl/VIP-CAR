from sqlalchemy import String, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin


class VipParkingSpot(Base, TimestampMixin):
    __tablename__ = "vip_parking_spots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spot_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="车位编号")
    owner: Mapped[str | None] = mapped_column(String(50), comment="所属人")
    allowed_plates: Mapped[str] = mapped_column(Text, nullable=False, comment="允许车牌JSON数组")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用 0停用")

    notify_configs: Mapped[list["SpotNotifyConfig"]] = relationship(back_populates="spot", cascade="all, delete-orphan")
    alert_logs: Mapped[list["AlertLog"]] = relationship(back_populates="spot")
