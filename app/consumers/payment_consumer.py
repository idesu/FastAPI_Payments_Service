import logging

from faststream import AckPolicy
from faststream.rabbit import RabbitRouter, RabbitMessage

from app.consumers.deps import PaymentServiceFastStreamDep
from app.core.exceptions import WebhookDeliveryError
from app.core.rabbitmq import payments_queue, broker
from app.schemas.event import PaymentCreatedEvent

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
):
    try:
        event = PaymentCreatedEvent(**payload)
    except Exception as e:
        logger.error(f"Invalid event format: {e}")
        await msg.reject(requeue=False)  # payload невалидный, в DLQ
        return

    payment_id = event.payment_id
    retry_count = msg.headers.get("x-retry-count", 0)

    logger.info(f"Received payment {payment_id}, retry {retry_count}")

    try:
        await service.process_payment(
            payment_id=event.payment_id,
            webhook_url=event.webhook_url,
            amount=event.amount,
            currency=event.currency,
        )

        await msg.ack()  # всё успешно – подтверждаем
        logger.info(f"Payment {payment_id} processed and acked")

    except (
        WebhookDeliveryError
    ) as e:  # сервис упал на этапе отправки, три неудачных попытки - в dlq
        logger.error(f"Webhook error for {payment_id}: {e}")
        await msg.reject(requeue=False)

    except Exception as e:
        if retry_count >= 3:
            logger.error(f"Max retries exceeded for {payment_id}")
            await msg.reject(requeue=False)  # три попытки выполнены, в DLQ
        else:
            logger.exception(f"Unexpected error for {payment_id}: {e}")
            await msg.nack(requeue=False)  # удаляем текущее
            await broker.publish(  # и публикуем обратно с увеличенным счётчиком
                event.model_dump(),
                queue="payments.new",
                exchange="payments",
                routing_key="payment.created",
                headers={"x-retry-count": retry_count + 1},
            )
