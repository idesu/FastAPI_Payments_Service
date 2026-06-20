import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PaymentNotFound
from app.models.payment import PaymentStatus
from app.repositories.outbox import OutboxRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentResponse


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        payment_repo: PaymentRepository,
        outbox_repo: OutboxRepository,
    ):
        self._session = session
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo

    async def create_payment(
        self, idempotency_key: str, data: PaymentCreate
    ) -> PaymentResponse:
        # Проверка идемпотентности
        existing = await self._payment_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return PaymentResponse.model_validate(existing)

        # Создание платежа
        payment = await self._payment_repo.create(
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            payment_metadata=data.metadata if data.metadata else None,
            idempotency_key=idempotency_key,
            webhook_url=str(data.webhook_url),
            status=PaymentStatus.PENDING,
        )

        event_payload = {
            "payment_id": str(payment.id),
            "amount": str(payment.amount),
            "currency": payment.currency,
            "webhook_url": payment.webhook_url,
        }
        # Сохраняем событие в outbox
        await self._outbox_repo.create(
            event_type="payment.created",
            payload=json.dumps(event_payload),
        )

        await self._session.commit()
        return PaymentResponse.model_validate(payment)

    async def get_payment(self, payment_id: UUID) -> PaymentResponse:
        payment = await self._payment_repo.get(payment_id)
        if not payment:
            raise PaymentNotFound(f"Payment {payment_id} not found")
        return PaymentResponse.model_validate(payment)

    async def update_payment_status(
        self, payment_id: UUID, status: PaymentStatus
    ) -> None:
        payment = await self._payment_repo.get(payment_id)
        if payment:
            await self._payment_repo.update(payment, status=status)
            await self._session.commit()
