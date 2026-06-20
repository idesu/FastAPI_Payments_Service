import asyncio
import logging

from app.core.config import settings
from app.core.database import db_helper
from app.core.exceptions import OutboxPublishError
from app.core.rabbitmq import broker
from app.core.rabbitmq import declare_topology
from app.services.outbox_publisher import OutboxPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()


async def run_publisher():
    while not shutdown_event.is_set():
        try:
            async with db_helper.session_factory() as session:
                publisher = OutboxPublisher(session)
                count = await publisher.publish_pending_events()
                if count:
                    logger.info(f"Published {count} outbox events")
        except OutboxPublishError as e:
            logger.error(f"Outbox publish error: {e}")
            await asyncio.sleep(settings.OUTBOX_PUBLISH_INTERVAL)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)

        try:
            await asyncio.wait_for(
                shutdown_event.wait(), timeout=settings.OUTBOX_PUBLISH_INTERVAL
            )
        except asyncio.TimeoutError:
            pass


async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: shutdown_event.set())

    # Подключаемся и объявляем очереди
    await broker.connect()
    await declare_topology()

    try:
        await run_publisher()
    finally:
        await broker.stop()
        await db_helper.dispose()
        logger.info("Outbox worker gracefully stopped")


if __name__ == "__main__":
    asyncio.run(main())
