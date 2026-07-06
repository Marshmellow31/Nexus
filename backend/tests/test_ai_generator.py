"""Tests for the AI workflow generator with a stubbed AI provider."""

from __future__ import annotations

import json
import pytest

from app.modules.ai.generator import WorkflowGenerator, _extract_json, _normalise
from app.modules.ai.service import AIRequest, AIResponse, AIService
from app.modules.nodes import register_builtin_nodes
from app.modules.nodes.registry import NodeRegistry, registry

register_builtin_nodes()


class StubProvider:
    """Returns a hardcoded valid workflow JSON without calling any LLM."""

    def __init__(self, payload: dict):
        self._payload = payload

    async def complete(self, req: AIRequest) -> AIResponse:
        return AIResponse(
            text=json.dumps(self._payload),
            data=self._payload,
            model="stub",
        )


VALID_WORKFLOW = {
    "name": "AI Summary",
    "description": "Summarise HTTP response with AI",
    "nodes": [
        {"id": "n1", "type": "http.request", "config": {"url": "https://example.com"}, "position": {"x": 100, "y": 100}},
        {"id": "n2", "type": "ai.generate", "config": {"prompt": "{{ nodes.n1.output.body }}"}, "position": {"x": 320, "y": 100}},
    ],
    "edges": [{"source": "n1", "target": "n2"}],
}


@pytest.mark.asyncio
async def test_generator_returns_valid_dag():
    gen = WorkflowGenerator(AIService(StubProvider(VALID_WORKFLOW)), registry)
    result = await gen.generate("Summarise a URL with AI")
    assert result["name"] == "AI Summary"
    assert len(result["nodes"]) == 2
    assert result["nodes"][0]["type"] == "http.request"


@pytest.mark.asyncio
async def test_generator_normalises_missing_positions():
    payload = {
        "name": "Test",
        "description": "desc",
        "nodes": [
            {"id": "a", "type": "action.store", "config": {"content": "hello"}},
        ],
        "edges": [],
    }
    gen = WorkflowGenerator(AIService(StubProvider(payload)), registry)
    result = await gen.generate("Store something")
    assert "position" in result["nodes"][0]


@pytest.mark.asyncio
async def test_generator_rejects_unknown_node_type():
    bad_payload = {
        "name": "Bad",
        "description": "",
        "nodes": [{"id": "x", "type": "nonexistent.node", "config": {}}],
        "edges": [],
    }
    gen = WorkflowGenerator(AIService(StubProvider(bad_payload)), registry)
    with pytest.raises(Exception):
        await gen.generate("do something")


def test_extract_json_from_prose():
    text = 'Sure! Here is the JSON:\n\n{"name": "test", "nodes": [], "edges": []}\n\nLet me know!'
    result = _extract_json(text)
    assert result is not None
    assert result["name"] == "test"


def test_catalogue_contains_all_node_types():
    gen = WorkflowGenerator(AIService(StubProvider({})), registry)
    cat = gen._build_catalogue()
    for spec in registry.all_specs():
        assert spec["type"] in cat
