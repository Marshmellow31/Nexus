"""Workflow CRUD service."""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, PermissionError
from app.modules.engine.graph import WorkflowGraph
from app.modules.workflows.models import Workflow


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        description: str | None = None,
        trigger_type: str = "manual",
        definition: dict,
    ) -> Workflow:
        # Validate the DAG before persisting
        WorkflowGraph.from_definition(definition)
        wf = Workflow(
            user_id=user_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            definition=definition,
            webhook_secret=secrets.token_urlsafe(32) if trigger_type == "webhook" else None,
        )
        self._session.add(wf)
        await self._session.flush()
        await self._session.refresh(wf)
        return wf

    async def list_for_user(self, user_id: uuid.UUID) -> list[Workflow]:
        result = await self._session.execute(
            select(Workflow)
            .where(Workflow.user_id == user_id)
            .order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, workflow_id: uuid.UUID, user_id: uuid.UUID) -> Workflow:
        result = await self._session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        wf = result.scalar_one_or_none()
        if not wf:
            raise NotFoundError(f"Workflow {workflow_id} not found")
        if wf.user_id != user_id:
            raise PermissionError("Access denied")
        return wf

    async def update(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        definition: dict | None = None,
        is_active: bool | None = None,
    ) -> Workflow:
        wf = await self.get(workflow_id, user_id)
        if name is not None:
            wf.name = name
        if description is not None:
            wf.description = description
        if definition is not None:
            WorkflowGraph.from_definition(definition)
            wf.definition = definition
            wf.version += 1
        if is_active is not None:
            wf.is_active = is_active
        await self._session.flush()
        await self._session.refresh(wf)
        return wf

    async def delete(self, workflow_id: uuid.UUID, user_id: uuid.UUID) -> None:
        wf = await self.get(workflow_id, user_id)
        await self._session.delete(wf)
        await self._session.flush()
