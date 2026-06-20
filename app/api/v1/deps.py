from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.outbox import OutboxRepository
from app.repositories.payment import PaymentRepository
from app.services.payment import PaymentService

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_payment_repository(session: SessionDep) -> PaymentRepository:
    return PaymentRepository(session)


def get_outbox_repository(session: SessionDep) -> OutboxRepository:
    return OutboxRepository(session)


PaymentRepositoryDep = Annotated[PaymentRepository, Depends(get_payment_repository)]
OutboxRepositoryDep = Annotated[OutboxRepository, Depends(get_outbox_repository)]


def get_payment_service(
    session: SessionDep,
    payment_repo: PaymentRepositoryDep,
    outbox_repo: OutboxRepositoryDep,
) -> PaymentService:
    return PaymentService(
        session=session, payment_repo=payment_repo, outbox_repo=outbox_repo
    )


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
