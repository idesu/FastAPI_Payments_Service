from typing import List

from sqlalchemy import select, update, func

from app.models.outbox import Outbox, OutboxStatus
from app.repositories.base import BaseRepository


class OutboxRepository(BaseRepository[Outbox]):
    def __init__(self, session):
        super().__init__(session, Outbox)

    async def get_pending_events(self, limit: int = 100) -> List[Outbox]:
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING)
            .order_by(Outbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_sent(self, outbox_id):
        stmt = (
            update(Outbox)
            .where(Outbox.id == outbox_id)
            .values(status=OutboxStatus.SENT, sent_at=func.now())
        )
        await self.session.execute(stmt)
        await self.session.flush()
