from datetime import datetime
from sqlalchemy import String, Text, SmallInteger, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class AlertLog(Base):
    __tablename__ = "alert_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spot_id: Mapped[int] = mapped_column(Integer, ForeignKey("vip_parking_spots.id"), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False)
    sent_via: Mapped[str] = mapped_column(String(50), nullable=False, comment="成功通道逗号分隔")
    sent_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_resolved: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0未解决 1已解决")
    resolved_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)

    spot: Mapped["VipParkingSpot"] = relationship(back_populates="alert_logs")
