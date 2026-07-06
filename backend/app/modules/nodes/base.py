"""Node contract — the extensibility seam of the whole engine.

A node is a self-contained action. Its `NodeSpec` (static metadata + JSON Schemas)
drives THREE things with no duplication:
  1. Frontend config forms (rendered generically from `config_schema`).
  2. Server-side validation of node config.
  3. AI workflow generation (the LLM generates configs against these schemas).

Adding a capability to Nexus = adding one Node subclass. The core never changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class NodeSpec:
    type: str  # unique, dotted: "ai.generate", "http.request", "logic.condition"
    title: str
    category: str  # "trigger" | "ai" | "logic" | "action" | "integration"
    description: str
    # JSON Schema (draft 2020-12) for this node's config object.
    config_schema: dict[str, Any] = field(default_factory=dict)
    # JSON Schema describing the shape of `output` this node produces.
    output_schema: dict[str, Any] = field(default_factory=dict)
    # Connection provider required at execution time, e.g. "google", "github".
    requires_connection: str | None = None
    # Triggers start a workflow; they are not executed inside the DAG the normal way.
    is_trigger: bool = False
    icon: str = "sparkles"


class ExecutionContext:
    """Everything a node needs at run time, without coupling to HTTP or the DB layer.

    - `resolve(config)` expands `{{ nodes.<id>.output.<path> }}` templates against
      already-completed node outputs (data-only lookup, never eval).
    - `services` is a small container (AI service, credential vault, http client)
      injected by the executor so nodes stay unit-testable.
    """

    def __init__(
        self,
        *,
        run_id: str,
        user_id: str,
        trigger_payload: dict[str, Any],
        node_outputs: dict[str, dict[str, Any]],
        services: Any,
        resolver: Any,
    ):
        self.run_id = run_id
        self.user_id = user_id
        self.trigger_payload = trigger_payload
        self.node_outputs = node_outputs
        self.services = services
        self._resolver = resolver

    def resolve(self, config: dict[str, Any]) -> dict[str, Any]:
        return self._resolver.resolve(config, self.node_outputs, self.trigger_payload)


class Node(ABC):
    """Base class. Subclasses set `spec` and implement `execute`."""

    spec: ClassVar[NodeSpec]

    @abstractmethod
    async def execute(
        self, ctx: ExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Return this node's output dict. `config` is already template-resolved."""
        raise NotImplementedError
