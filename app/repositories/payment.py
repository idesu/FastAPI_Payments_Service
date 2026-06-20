from typing import Optional

from sqlalchemy import select

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session):
        super().__init__(session, Payment)

    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.idempotency_key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
