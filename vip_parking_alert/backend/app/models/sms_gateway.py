from sqlalchemy import String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class SmsGatewayConfig(Base, TimestampMixin):
    __tablename__ = "sms_gateway_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(50), comment="网关名称")
    url: Mapped[str] = mapped_column(String(255), nullable=False, comment="API基础URL")
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    from_param: Mapped[str] = mapped_column(String(50), nullable=False, comment="发送方标识")
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
