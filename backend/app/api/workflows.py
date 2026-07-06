"""Workflow CRUD routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import WorkflowCreate, WorkflowOut, WorkflowUpdate
from app.core.db import get_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.workflows.service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _svc(session: AsyncSession = Depends(get_session)) -> WorkflowService:
    return WorkflowService(session)


@router.get("", response_model=list[WorkflowOut])
async def list_workflows(
    user: User = Depends(get_current_user),
    svc: WorkflowService = Depends(_svc),
):
    return await svc.list_for_user(user.id)


@router.post("", response_model=WorkflowOut, status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    user: User = Depends(get_current_user),
    svc: WorkflowService = Depends(_svc),
):
    return await svc.create(
        user.id,
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        definition=body.definition,
    )


@router.get("/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: uuid.UUID,
    user: User = Depends(get_current_user),
    svc: WorkflowService = Depends(_svc),
):
    return await svc.get(workflow_id, user.id)


@router.patch("/{workflow_id}", response_model=WorkflowOut)
async def update_workflow(
    workflow_id: uuid.UUID,
    body: WorkflowUpdate,
    user: User = Depends(get_current_user),
    svc: WorkflowService = Depends(_svc),
):
    return await svc.update(
        workflow_id,
        user.id,
        name=body.name,
        description=body.description,
        definition=body.definition,
        is_active=body.is_active,
    )


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: uuid.UUID,
    user: User = Depends(get_current_user),
    svc: WorkflowService = Depends(_svc),
):
    await svc.delete(workflow_id, user.id)
