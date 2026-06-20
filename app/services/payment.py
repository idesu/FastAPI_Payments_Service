import asyncio
import datetime
import json
import logging
import random
from decimal import Decimal
from uuid import UUID

from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PaymentNotFound, WebhookDeliveryError
from app.models.payment import PaymentStatus
from app.repositories.outbox import OutboxRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.webhook import WebhookSender

logger = logging.getLogger(__name__)


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
        self,
        payment_id: UUID,
        status: PaymentStatus,
    ) -> None:
        payment = await self._payment_repo.get(payment_id)
        if payment:
            await self._payment_repo.update(payment, status=status)
            await self._session.commit()

    async def process_payment(
        self,
        payment_id: UUID,
        webhook_url: HttpUrl,
        amount: Decimal,
        currency: str,
    ) -> None:
        """
        Полный цикл обработки платежа: эмуляция, обновление статуса, отправка webhook.
        При ошибках поднимает исключения, которые обрабатываются в consumer.
        """
        logger.info(f"Processing payment {payment_id}")
        status = await self._payment_emulation(
            str(payment_id), str(webhook_url), str(amount), str(currency)
        )
        await self.update_payment_status(payment_id, status)

        webhook_payload = {
            "payment_id": str(payment_id),
            "status": status.value,
            "processed_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        async with WebhookSender() as webhook_sender:
            sent = await webhook_sender.send_with_retries(
                str(webhook_url), webhook_payload
            )

        if not sent:
            raise WebhookDeliveryError(
                f"Webhook delivery failed for payment {payment_id}"
            )

        logger.info(f"Payment {payment_id} processed successfully, status={status}")

    async def _payment_emulation(*args, **kwargs):
        delay = random.uniform(2.0, 5.0)
        await asyncio.sleep(delay)

        success = random.random() < 0.9
        return PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
