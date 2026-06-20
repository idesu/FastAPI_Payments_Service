import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict
from uuid import UUID, uuid4

from sqlalchemy import String, Numeric, Enum as SAEnum, JSON, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins.created_at import get_current_dt, CreatedAtMixin


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(CreatedAtMixin, Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=get_current_dt,
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_payments_idempotency_key",
            "idempotency_key",
            postgresql_where=(status == PaymentStatus.PENDING),
        ),
    )
