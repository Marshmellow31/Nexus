"""The executor — runs a workflow graph node-by-node with retries, timeouts,
per-node checkpointing, and branch pruning.

Design notes:
- Runs in the WORKER process, never in an API request.
- Checkpoints every node result via the injected `RunStore` so a crashed worker
  leaves accurate history and (future) can resume.
- Branch pruning: a condition node returns {"result": bool}; edges from its
  "true"/"false" handle decide which downstream nodes become reachable.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import settings
from app.modules.engine.graph import WorkflowGraph
from app.modules.engine.resolver import TemplateResolver
from app.modules.nodes.base import ExecutionContext
from app.modules.nodes.registry import NodeRegistry


class RunStore(Protocol):
    """Persistence seam. Real impl writes to Postgres; tests use an in-memory stub."""

    async def start_step(self, run_id: str, node_id: str, node_type: str) -> None: ...
    async def finish_step(
        self, run_id: str, node_id: str, *, output: dict, attempts: int, ms: int
    ) -> None: ...
    async def fail_step(
        self, run_id: str, node_id: str, *, error: str, attempts: int, ms: int
    ) -> None: ...
    async def mark_run(self, run_id: str, status: str, error: str | None = None) -> None: ...


@dataclass
class NodePolicy:
    max_attempts: int
    timeout_seconds: int
    backoff_base: float = 0.5


class Executor:
    def __init__(
        self,
        registry: NodeRegistry,
        store: RunStore,
        services: Any,
        resolver: TemplateResolver | None = None,
    ):
        self.registry = registry
        self.store = store
        self.services = services
        self.resolver = resolver or TemplateResolver()

    async def run(
        self,
        *,
        run_id: str,
        user_id: str,
        graph: WorkflowGraph,
        trigger_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        node_outputs: dict[str, dict[str, Any]] = {}
        node_map = graph.node_map()
        order = graph.topological_order()
        skipped: set[str] = set()

        ctx = ExecutionContext(
            run_id=run_id,
            user_id=user_id,
            trigger_payload=trigger_payload or {},
            node_outputs=node_outputs,
            services=self.services,
            resolver=self.resolver,
        )

        await self.store.mark_run(run_id, "running")
        try:
            async with asyncio.timeout(settings.run_max_seconds):
                for node_id in order:
                    if node_id in skipped or self._is_unreachable(
                        node_id, graph, node_outputs, skipped
                    ):
                        skipped.add(node_id)
                        continue

                    gnode = node_map[node_id]
                    output = await self._run_node(ctx, gnode)
                    node_outputs[node_id] = output
                    self._prune_branches(node_id, output, graph, skipped)
        except TimeoutError:
            await self.store.mark_run(run_id, "failed", "Run exceeded time limit")
            raise
        except Exception as exc:  # node failure already recorded per-step
            await self.store.mark_run(run_id, "failed", str(exc))
            raise

        await self.store.mark_run(run_id, "succeeded")
        return node_outputs

    def _is_unreachable(
        self,
        node_id: str,
        graph: WorkflowGraph,
        outputs: dict[str, dict],
        skipped: set[str],
    ) -> bool:
        # A node with incoming edges is reachable only if at least one parent ran.
        incoming = [e for e in graph.edges if e.target == node_id]
        if not incoming:
            return False
        return all(e.source in skipped or e.source not in outputs for e in incoming)

    def _prune_branches(
        self,
        node_id: str,
        output: dict[str, Any],
        graph: WorkflowGraph,
        skipped: set[str],
    ) -> None:
        # Condition nodes emit {"result": bool}; drop the not-taken handle.
        if "result" not in output:
            return
        taken = "true" if output["result"] else "false"
        for e in graph.outgoing(node_id):
            if e.source_handle in ("true", "false") and e.source_handle != taken:
                skipped.add(e.target)

    async def _run_node(
        self, ctx: ExecutionContext, gnode
    ) -> dict[str, Any]:
        node = self.registry.create(gnode.type)
        policy = self._policy_for(gnode.config)
        await self.store.start_step(ctx.run_id, gnode.id, gnode.type)

        loop = asyncio.get_event_loop()
        start = loop.time()
        last_error: Exception | None = None

        for attempt in range(1, policy.max_attempts + 1):
            try:
                resolved = ctx.resolve(gnode.config)
                async with asyncio.timeout(policy.timeout_seconds):
                    output = await node.execute(ctx, resolved)
                ms = int((loop.time() - start) * 1000)
                await self.store.finish_step(
                    ctx.run_id, gnode.id, output=output, attempts=attempt, ms=ms
                )
                return output
            except Exception as exc:  # noqa: BLE001 - retry policy decides
                last_error = exc
                if attempt < policy.max_attempts:
                    await asyncio.sleep(policy.backoff_base * (2 ** (attempt - 1)))

        ms = int((loop.time() - start) * 1000)
        await self.store.fail_step(
            ctx.run_id,
            gnode.id,
            error=str(last_error),
            attempts=policy.max_attempts,
            ms=ms,
        )
        raise last_error  # type: ignore[misc]

    @staticmethod
    def _policy_for(config: dict[str, Any]) -> NodePolicy:
        meta = config.get("_policy", {}) if isinstance(config, dict) else {}
        return NodePolicy(
            max_attempts=int(meta.get("max_attempts", settings.node_default_max_attempts)),
            timeout_seconds=int(
                meta.get("timeout_seconds", settings.node_default_timeout_seconds)
            ),
        )
