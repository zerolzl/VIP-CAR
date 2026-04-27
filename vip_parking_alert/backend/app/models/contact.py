from sqlalchemy import String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
