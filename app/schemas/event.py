from pydantic import BaseModel, HttpUrl
from uuid import UUID
from decimal import Decimal


class PaymentCreatedEvent(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: str
    webhook_url: HttpUrl
