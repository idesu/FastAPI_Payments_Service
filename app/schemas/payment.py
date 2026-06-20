from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    currency: str = Field("RUB", pattern="^(RUB|USD|EUR)$")
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    id: UUID
    amount: Decimal
    currency: str
    description: Optional[str]
    metadata: Optional[Dict] = Field(None, alias="payment_metadata")
    status: PaymentStatus
    idempotency_key: str
    webhook_url: HttpUrl
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
