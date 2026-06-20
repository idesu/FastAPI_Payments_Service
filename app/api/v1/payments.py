from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.v1.deps import PaymentServiceDep
from app.core.config import settings
from app.core.dependencies import verify_api_key
from app.core.exceptions import PaymentNotFound
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix=settings.api.v1.prefix)


@router.post("/payments", status_code=202, response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    service: PaymentServiceDep,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    api_key: str = Depends(verify_api_key),
):
    """Создание платежа с идемпотентностью."""
    payment = await service.create_payment(idempotency_key, payment_data)
    return payment


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    service: PaymentServiceDep,
    api_key: str = Depends(verify_api_key),
):
    try:
        payment = await service.get_payment(payment_id)
    except PaymentNotFound:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
