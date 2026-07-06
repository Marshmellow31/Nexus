"""PostgresRunStore — implements the engine's RunStore protocol over SQLAlchemy.

Checkpoints every node after execution. The worker gets this injected; the
executor protocol stays clean (no SQLAlchemy import in engine code).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.runs.models import Run, RunStep


class PostgresRunStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def start_step(self, run_id: str, node_id: str, node_type: str) -> None:
        step = RunStep(
            id=uuid.uuid4(),
            run_id=uuid.UUID(run_id),
            node_id=node_id,
            node_type=node_type,
            status="running",
        )
        self._session.add(step)
        await self._session.flush()

    async def finish_step(
        self, run_id: str, node_id: str, *, output: dict, attempts: int, ms: int
    ) -> None:
        await self._session.execute(
            update(RunStep)
            .where(RunStep.run_id == uuid.UUID(run_id), RunStep.node_id == node_id)
            .values(status="succeeded", output=output, attempts=attempts, duration_ms=ms)
        )
        await self._session.flush()

    async def fail_step(
        self, run_id: str, node_id: str, *, error: str, attempts: int, ms: int
    ) -> None:
        await self._session.execute(
            update(RunStep)
            .where(RunStep.run_id == uuid.UUID(run_id), RunStep.node_id == node_id)
            .values(status="failed", error=error, attempts=attempts, duration_ms=ms)
        )
        await self._session.flush()

    async def mark_run(self, run_id: str, status: str, error: str | None = None) -> None:
        values: dict = {"status": status}
        if status == "running":
            values["started_at"] = datetime.now(timezone.utc)
        if status in ("succeeded", "failed", "cancelled"):
            values["finished_at"] = datetime.now(timezone.utc)
        if error:
            values["error"] = error
        await self._session.execute(
            update(Run).where(Run.id == uuid.UUID(run_id)).values(**values)
        )
        await self._session.flush()

    async def get_run(self, run_id: str) -> Run | None:
        result = await self._session.execute(
            select(Run).where(Run.id == uuid.UUID(run_id))
        )
        return result.scalar_one_or_none()
