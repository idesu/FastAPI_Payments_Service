import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins.created_at import CreatedAtMixin


class OutboxStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"


class Outbox(CreatedAtMixin, Base):
    __tablename__ = "outbox"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        SQLEnum(OutboxStatus),
        default=OutboxStatus.PENDING,
        nullable=False,
    )
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    retries: Mapped[int] = mapped_column(Integer, default=0)
