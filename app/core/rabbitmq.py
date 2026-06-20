import logging

import aio_pika
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, ExchangeType, RabbitQueue

from app.core.config import settings

logger = logging.getLogger(__name__)

broker = RabbitBroker(settings.rabbitmq_url.unicode_string())
app = FastStream(broker)


# Dead-letter exchange для необработанных сообщений
payments_dlx_exchange = RabbitExchange(
    name="payments.dlx",
    type=ExchangeType.DIRECT,
    durable=True,
)

# Очередь для дохлых сообщений
dead_queue = RabbitQueue(name="payments.dead", durable=True, routing_key="payment.dead")

# Основная очередь с привязкой DLX через аргументы
payments_queue = RabbitQueue(
    name=settings.rmq_payments_queue,
    routing_key="payment.created",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payment.dead",
        # опционально TTL, после которого необработанное сообщение уходит в DLX
        "x-message-ttl": 60000,
    },
)


@app.after_startup
async def declare_topology():
    """Объявляем обменники и очереди, биндинги создаются автоматически."""
    logger.info("Connected to RabbitMQ")
    dlx_exchange: aio_pika.RobustExchange = await broker.declare_exchange(
        payments_dlx_exchange
    )
    dlx_queue: aio_pika.RobustQueue = await broker.declare_queue(dead_queue)
    await broker.declare_queue(payments_queue)

    await dlx_queue.bind(
        exchange=dlx_exchange,
        routing_key="payment.dead",
    )
    logger.info("RabbitMQ queues and exchanges declared")
