from typing import Annotated

from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_helper
from app.repositories.outbox import OutboxRepository
from app.repositories.payment import PaymentRepository
from app.services.payment import PaymentService

SessionDep = Annotated[AsyncSession, Depends(db_helper.session_getter)]


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
        session=session,
        payment_repo=payment_repo,
        outbox_repo=outbox_repo,
    )


PaymentServiceFastStreamDep = Annotated[PaymentService, Depends(get_payment_service)]
