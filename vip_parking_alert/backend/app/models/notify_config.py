from sqlalchemy import String, SmallInteger, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin


class SpotNotifyConfig(Base, TimestampMixin):
    __tablename__ = "spot_notify_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spot_id: Mapped[int] = mapped_column(Integer, ForeignKey("vip_parking_spots.id"), nullable=False)
    notify_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="sms或webhook")
    target: Mapped[str] = mapped_column(String(255), nullable=False, comment="手机号或Webhook URL")
    contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=True)
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1)

    spot: Mapped["VipParkingSpot"] = relationship(back_populates="notify_configs")
    contact: Mapped["Contact | None"] = relationship()
