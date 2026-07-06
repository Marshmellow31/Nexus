"""arq worker entrypoint. This process — not the API — executes workflows.

Run:  arq app.workers.main.WorkerSettings
The API enqueues `execute_workflow(run_id)`; the worker loads the run + graph from
Postgres, executes it through the Executor, and checkpoints each step back.
"""

from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings

from app.core.config import settings
from app.modules.nodes import register_builtin_nodes


async def startup(ctx: dict[str, Any]) -> None:
    # Import all ORM models so relationship strings ("User", "Workflow", …) resolve.
    from app.modules.auth import models as _auth_models  # noqa: F401
    from app.modules.integrations import models as _integration_models  # noqa: F401
    from app.modules.runs import models as _run_models  # noqa: F401
    from app.modules.workflows import models as _workflow_models  # noqa: F401

    register_builtin_nodes()
    import httpx

    ctx["http"] = httpx.AsyncClient(timeout=30, follow_redirects=True)


async def shutdown(ctx: dict[str, Any]) -> None:
    client = ctx.get("http")
    if client is not None:
        await client.aclose()


async def execute_workflow(ctx: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Fully wired job: loads run + workflow from Postgres, executes the graph."""
    import httpx
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.modules.ai.service import AIService, LiteLLMProvider
    from app.modules.engine.executor import Executor
    from app.modules.engine.graph import WorkflowGraph
    from app.modules.engine.services import NodeServices
    from app.modules.integrations.vault import CredentialVault
    from app.modules.nodes.registry import registry
    from app.modules.runs.models import Run
    from app.modules.runs.store import PostgresRunStore

    async with SessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            return {"error": f"Run {run_id} not found"}

        definition = run.definition_snapshot or {}
        graph = WorkflowGraph.from_definition(definition)
        store = PostgresRunStore(session)
        vault = CredentialVault(session)

        async def get_credentials(connection_id: str) -> dict:
            return await vault.get_credentials(connection_id, run.user_id)

        services = NodeServices(
            ai=AIService(LiteLLMProvider()),
            http=ctx.get("http") or httpx.AsyncClient(timeout=30),
            get_credentials=get_credentials,
        )

        executor = Executor(registry, store, services)
        try:
            outputs = await executor.run(
                run_id=run_id,
                user_id=str(run.user_id),
                graph=graph,
                trigger_payload=run.trigger_payload or {},
            )
        except Exception as exc:
            # Executor already marked the run/step failed — persist that status.
            await session.commit()
            return {"run_id": run_id, "status": "failed", "error": str(exc)}
        await session.commit()
        return {"run_id": run_id, "status": "succeeded", "steps": len(outputs)}


class WorkerSettings:
    functions = [execute_workflow]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = settings.run_max_seconds + 30


if __name__ == "__main__":
    from arq import run_worker

    run_worker(WorkerSettings)
