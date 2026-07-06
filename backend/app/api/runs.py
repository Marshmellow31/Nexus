"""Run routes — trigger execution, query history, SSE status stream."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.schemas import RunOut, RunSummaryOut, RunTrigger
from app.core.db import SessionLocal, get_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.runs.service import RunService
from app.modules.workflows.service import WorkflowService

router = APIRouter(prefix="/runs", tags=["runs"])


def _run_svc(session: AsyncSession = Depends(get_session)) -> RunService:
    return RunService(session)


def _wf_svc(session: AsyncSession = Depends(get_session)) -> WorkflowService:
    return WorkflowService(session)


@router.get("", response_model=list[RunSummaryOut])
async def list_recent_runs(
    user: User = Depends(get_current_user),
    svc: RunService = Depends(_run_svc),
):
    return await svc.list_for_user(user.id)


@router.get("/{run_id}", response_model=RunOut)
async def get_run(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    svc: RunService = Depends(_run_svc),
):
    return await svc.get(run_id, user.id)


@router.post("/workflows/{workflow_id}/trigger", response_model=RunSummaryOut, status_code=202)
async def trigger_run(
    workflow_id: uuid.UUID,
    body: RunTrigger,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a run row (status=pending) and enqueue the arq job."""
    wf_svc = WorkflowService(session)
    wf = await wf_svc.get(workflow_id, user.id)

    run_svc = RunService(session)
    run = await run_svc.create(
        workflow_id=workflow_id,
        user_id=user.id,
        trigger_payload=body.trigger_payload,
        definition_snapshot=wf.definition,
    )

    # Enqueue to arq worker. Redis connection is created per-request here;
    # in a high-traffic scenario move to a shared pool in app state.
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        from app.core.config import settings

        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await pool.enqueue_job("execute_workflow", str(run.id))
        await pool.aclose()
    except Exception:
        # Worker not running (local dev without Redis) — mark as failed gracefully
        from sqlalchemy import update

        from app.modules.runs.models import Run

        await session.execute(
            update(Run)
            .where(Run.id == run.id)
            .values(status="failed", error="Worker unavailable — is Redis running?")
        )

    return run


@router.get("/{run_id}/stream")
async def stream_run_status(
    run_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Server-Sent Events stream for live run status updates.

    Polls every second (simple, no pub/sub needed at this scale).
    Closes when the run reaches a terminal state or client disconnects.
    """

    async def event_generator():
        terminal = {"succeeded", "failed", "cancelled"}
        async with SessionLocal() as session:
            svc = RunService(session)
            while True:
                if await request.is_disconnected():
                    break
                try:
                    run = await svc.get(run_id, user.id)
                    data = {
                        "run_id": str(run.id),
                        "status": run.status,
                        "steps": [
                            {
                                "node_id": s.node_id,
                                "status": s.status,
                                "duration_ms": s.duration_ms,
                            }
                            for s in run.steps
                        ],
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    yield {"event": "status", "data": json.dumps(data)}
                    if run.status in terminal:
                        yield {"event": "done", "data": json.dumps({"status": run.status})}
                        break
                except Exception as exc:
                    yield {"event": "error", "data": json.dumps({"message": str(exc)})}
                    break
                await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
