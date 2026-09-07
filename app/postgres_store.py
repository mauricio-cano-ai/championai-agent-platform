from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain import TaskView
from app.store import TaskStore


class Base(DeclarativeBase):
    pass


class TaskRow(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ActionClaimRow(Base):
    __tablename__ = "action_claims"

    action_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    claimed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PostgresTaskStore(TaskStore):
    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(database_url, pool_pre_ping=True)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _session(self) -> AsyncSession:
        return self.sessions()

    @staticmethod
    def _decode(row: TaskRow | None) -> TaskView | None:
        if row is None:
            return None
        return TaskView.model_validate_json(row.payload_json)

    async def get_by_idempotency_key(self, key: str) -> TaskView | None:
        async with self.sessions() as session:
            row = await session.scalar(select(TaskRow).where(TaskRow.idempotency_key == key))
            return self._decode(row)

    async def save(self, task: TaskView) -> TaskView:
        async with self.sessions() as session:
            row = await session.get(TaskRow, task.id)
            payload = task.model_dump_json()
            if row is None:
                row = TaskRow(id=task.id, idempotency_key=task.idempotency_key, payload_json=payload)
                session.add(row)
            else:
                row.payload_json = payload
                row.updated_at = datetime.utcnow()
            await session.commit()
            return task

    async def get(self, task_id: str) -> TaskView | None:
        async with self.sessions() as session:
            return self._decode(await session.get(TaskRow, task_id))

    async def claim_action(self, action_id: str) -> bool:
        async with self.sessions() as session:
            if await session.get(ActionClaimRow, action_id):
                return False
            session.add(ActionClaimRow(action_id=action_id))
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                return False
            return True
