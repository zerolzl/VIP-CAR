from sqlalchemy import String, SmallInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class ExternalDbConfig(Base, TimestampMixin):
    __tablename__ = "external_db_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="配置名称")
    db_type: Mapped[str] = mapped_column(String(20), default="mssql")
    host: Mapped[str] = mapped_column(String(100), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="AES加密存储")
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
