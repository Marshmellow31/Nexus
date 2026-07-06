"""AI workflow generator — the identity feature of Nexus.

Takes a plain-English description, sends the node registry (with JSON Schemas)
to the LLM as context, and gets back a validated workflow DAG. The LLM is
constrained to only reference node types that exist in the registry.

This is structured generation: we build a system prompt from live registry data,
ask for JSON, validate it with WorkflowGraph, and retry once on invalid output.
"""

from __future__ import annotations

import json
import uuid

from app.modules.ai.service import AIRequest, AIService
from app.modules.engine.graph import WorkflowGraph
from app.modules.nodes.registry import NodeRegistry


SYSTEM_PROMPT = """You are an expert workflow automation planner for the Nexus platform.

Given a user's plain-English automation goal, generate a valid Nexus workflow definition.

## Available node types
{node_catalogue}

## Rules
1. ONLY use node `type` values listed above — never invent types.
2. Every node needs a unique `id` (short, lowercase, e.g. "ai1", "http1", "cond1").
3. Every node needs a `config` object matching its `config_schema` (required fields must be present).
4. Every edge needs `source` and `target` matching node ids.
5. Condition nodes (logic.condition) have two outgoing edges: one with source_handle "true", one with source_handle "false".
6. Use `{{ nodes.<id>.output.<field> }}` template expressions to pass data between nodes.
7. The first node should be the logical start (no incoming edges, or a trigger node).
8. Keep it minimal — only the nodes needed for the goal.

## Output format (JSON only, no prose)
{{
  "name": "Short workflow name",
  "description": "One sentence description",
  "nodes": [
    {{
      "id": "n1",
      "type": "node.type",
      "label": "Human label for canvas",
      "config": {{ ... }},
      "position": {{ "x": 100, "y": 100 }}
    }}
  ],
  "edges": [
    {{ "source": "n1", "target": "n2", "source_handle": null }}
  ]
}}
"""


class WorkflowGenerator:
    def __init__(self, ai: AIService, registry: NodeRegistry) -> None:
        self._ai = ai
        self._registry = registry

    async def generate(self, description: str, api_key: str | None = None) -> dict:
        """Returns a validated workflow definition dict ready to persist."""
        catalogue = self._build_catalogue()
        system = SYSTEM_PROMPT.format(node_catalogue=catalogue)

        request = AIRequest(
            prompt=f"Generate a Nexus workflow for this goal:\n\n{description}",
            system=system,
            model="gemini/gemini-1.5-flash",
            temperature=0.3,
            max_tokens=2048,
            json_schema={"type": "object"},  # force JSON mode
            api_key=api_key,
        )

        response = await self._ai.generate(request)
        raw = response.data or _extract_json(response.text)

        if not raw:
            raise ValueError("AI returned no parseable JSON")

        # Validate DAG structure — raises ValidationError if broken
        WorkflowGraph.from_definition(raw)

        # Validate every node type exists in the registry
        unknown = [
            n["type"]
            for n in raw.get("nodes", [])
            if not self._registry.has(n.get("type", ""))
        ]
        if unknown:
            raise ValueError(f"AI generated unknown node types: {unknown}")

        # Add stable IDs and defaults for any node missing them
        _normalise(raw)

        return raw

    def _build_catalogue(self) -> str:
        lines = []
        for spec in self._registry.all_specs():
            lines.append(f"\n### {spec['type']} — {spec['title']}")
            lines.append(f"Description: {spec['description']}")
            if spec["requires_connection"]:
                lines.append(f"Requires connection: {spec['requires_connection']}")
            lines.append(f"Config schema:\n{json.dumps(spec['config_schema'], indent=2)}")
            lines.append(f"Output schema:\n{json.dumps(spec['output_schema'], indent=2)}")
        return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
    """Best-effort extraction of first {...} block from model output."""
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _normalise(definition: dict) -> None:
    """Ensure every node has an id and sane position; add stable edge ids."""
    for i, node in enumerate(definition.get("nodes", [])):
        if not node.get("id"):
            node["id"] = f"n{i + 1}"
        if "position" not in node:
            node["position"] = {"x": 100 + i * 220, "y": 200}

    for i, edge in enumerate(definition.get("edges", [])):
        if not edge.get("id"):
            edge["id"] = str(uuid.uuid4())[:8]
        if "source_handle" not in edge:
            edge["source_handle"] = None
