"""Run service — enqueue executions and query history."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, PermissionError
from app.modules.runs.models import Run, RunStep


class RunService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        trigger_type: str = "manual",
        trigger_payload: dict | None = None,
        definition_snapshot: dict | None = None,
    ) -> Run:
        run = Run(
            workflow_id=workflow_id,
            user_id=user_id,
            trigger_type=trigger_type,
            trigger_payload=trigger_payload,
            definition_snapshot=definition_snapshot,
            status="pending",
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get(self, run_id: uuid.UUID, user_id: uuid.UUID) -> Run:
        result = await self._session.execute(
            select(Run)
            .where(Run.id == run_id)
            .options(selectinload(Run.steps))
        )
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError(f"Run {run_id} not found")
        if run.user_id != user_id:
            raise PermissionError("Access denied")
        return run

    async def list_for_workflow(
        self, workflow_id: uuid.UUID, user_id: uuid.UUID, limit: int = 50
    ) -> list[Run]:
        result = await self._session.execute(
            select(Run)
            .where(Run.workflow_id == workflow_id, Run.user_id == user_id)
            .order_by(Run.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_user(self, user_id: uuid.UUID, limit: int = 20) -> list[Run]:
        result = await self._session.execute(
            select(Run)
            .where(Run.user_id == user_id)
            .order_by(Run.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
