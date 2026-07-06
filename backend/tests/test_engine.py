"""Proves the engine executes a real multi-node graph: template passing, an AI
node (faked), a condition branch with pruning, and per-node checkpointing."""

from __future__ import annotations

import pytest

from app.modules.ai.service import AIResponse, AIService
from app.modules.engine.executor import Executor
from app.modules.engine.graph import WorkflowGraph
from app.modules.engine.services import NodeServices
from app.modules.nodes import register_builtin_nodes
from app.modules.nodes.registry import registry

register_builtin_nodes()


class InMemoryStore:
    def __init__(self) -> None:
        self.steps: dict[str, dict] = {}
        self.run_status: str | None = None

    async def start_step(self, run_id, node_id, node_type):
        self.steps[node_id] = {"type": node_type, "status": "running"}

    async def finish_step(self, run_id, node_id, *, output, attempts, ms):
        self.steps[node_id].update(status="succeeded", output=output, attempts=attempts)

    async def fail_step(self, run_id, node_id, *, error, attempts, ms):
        self.steps[node_id].update(status="failed", error=error, attempts=attempts)

    async def mark_run(self, run_id, status, error=None):
        self.run_status = status


class FakeProvider:
    async def complete(self, req):
        return AIResponse(text=f"SUMMARY::{req.prompt}", model=req.model)


def _services() -> NodeServices:
    return NodeServices(ai=AIService(FakeProvider()), http=None)


@pytest.mark.asyncio
async def test_linear_flow_with_templates():
    definition = {
        "nodes": [
            {"id": "a", "type": "ai.generate", "config": {"prompt": "{{ trigger.subject }}"}},
            {
                "id": "b",
                "type": "action.store",
                "config": {"content": "{{ nodes.a.output.text }}"},
            },
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    graph = WorkflowGraph.from_definition(definition)
    store = InMemoryStore()
    ex = Executor(registry, store, _services())

    outputs = await ex.run(
        run_id="r1",
        user_id="u1",
        graph=graph,
        trigger_payload={"subject": "Meeting Tuesday"},
    )

    assert outputs["a"]["text"] == "SUMMARY::Meeting Tuesday"
    assert outputs["b"]["content"] == "SUMMARY::Meeting Tuesday"
    assert store.run_status == "succeeded"
    assert store.steps["b"]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_condition_prunes_untaken_branch():
    definition = {
        "nodes": [
            {
                "id": "cond",
                "type": "logic.condition",
                "config": {"left": "5", "operator": "gt", "right": "3"},
            },
            {"id": "yes", "type": "action.store", "config": {"content": "took true"}},
            {"id": "no", "type": "action.store", "config": {"content": "took false"}},
        ],
        "edges": [
            {"source": "cond", "target": "yes", "source_handle": "true"},
            {"source": "cond", "target": "no", "source_handle": "false"},
        ],
    }
    graph = WorkflowGraph.from_definition(definition)
    store = InMemoryStore()
    ex = Executor(registry, store, _services())

    outputs = await ex.run(run_id="r2", user_id="u1", graph=graph)

    assert outputs["cond"]["result"] is True
    assert "yes" in outputs
    assert "no" not in outputs  # false branch pruned


@pytest.mark.asyncio
async def test_cycle_is_rejected():
    definition = {
        "nodes": [
            {"id": "a", "type": "action.store", "config": {"content": "x"}},
            {"id": "b", "type": "action.store", "config": {"content": "y"}},
        ],
        "edges": [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a"},
        ],
    }
    with pytest.raises(Exception):
        WorkflowGraph.from_definition(definition)
