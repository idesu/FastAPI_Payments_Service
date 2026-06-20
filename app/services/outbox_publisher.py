import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import OutboxPublishError
from app.core.rabbitmq import broker
from app.repositories.outbox import OutboxRepository

logger = logging.getLogger(__name__)


class OutboxPublisher:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OutboxRepository(session)

    async def publish_pending_events(self) -> int:
        events = await self.repo.get_pending_events(limit=100)
        if not events:
            return 0

        published = 0
        for event in events:
            try:
                await broker.publish(
                    json.loads(event.payload), queue=settings.rmq_payments_queue
                )
                await self.repo.mark_sent(event.id)
                published += 1
            except Exception as e:
                logger.error(f"Failed to publish outbox event {event.id}: {e}")
                raise OutboxPublishError(
                    f"Failed to publish event {event.id}: {e}"
                ) from e
        await self.session.commit()
        return published
