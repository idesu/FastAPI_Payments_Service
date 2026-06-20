import asyncio
import datetime
import logging
import random

from faststream import AckPolicy
from faststream.rabbit import RabbitRouter, RabbitMessage

from app.consumers.deps import PaymentServiceFastStreamDep, WebhookSenderDep
from app.core.config import settings
from app.core.exceptions import WebhookDeliveryError
from app.core.rabbitmq import payments_queue, broker
from app.models.payment import PaymentStatus

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(
    payments_queue,
    ack_policy=AckPolicy.MANUAL,
)
async def process_payment(
    payload: dict,
    msg: RabbitMessage,
    service: PaymentServiceFastStreamDep,
    webhook_sender: WebhookSenderDep,
):
    retry_count = msg.headers.get("x-retry-count", 0)

    try:
        # TODO: Добавить схему
        payment_id = payload.get("payment_id")
        webhook_url = payload.get("webhook_url")
        logger.info(f"Processing payment {payment_id}")
        status = await payment_emulation(payment_id)

        # Обновление статуса в БД
        await service.update_payment_status(payment_id, status)

        # Отправка уведомлений через вебхук с ретраями
        webhook_payload = {
            "payment_id": str(payment_id),
            "status": status.value,
            "processed_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        try:
            await webhook_sender.send_with_retries(webhook_url, webhook_payload)
        except Exception as e:
            raise WebhookDeliveryError(f"Webhook failed for payment {payment_id}: {e}")

        logger.info(f"Payment {payment_id} processed and webhook sent")
        await msg.ack()
        return
    except Exception as e:
        logger.error(f"Error processing payment {payload.get('payment_id')}: {e}")
        if retry_count >= 3:
            logger.error(f"Max retries exceeded for message. Sending to DLQ.")
            await msg.reject(requeue=False)
            return

        new_retry_count = retry_count + 1
        logger.warning(f"Retrying message (attempt {new_retry_count})...")

        # Публикуем сообщение заново с обновленным заголовком
        await broker.publish(
            payload,
            queue=settings.rmq_payments_queue,
            headers={"x-retry-count": new_retry_count},
        )
        await msg.ack()


async def payment_emulation(*args, **kwargs):
    delay = random.uniform(2.0, 5.0)
    await asyncio.sleep(delay)

    success = random.random() < 0.9
    return PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
