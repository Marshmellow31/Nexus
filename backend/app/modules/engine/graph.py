"""Workflow graph model + validation + topological ordering.

A workflow's definition is stored as JSON: a list of nodes and a list of edges.
The engine treats it as a DAG. Sequential execution today = topo-sort then run one
at a time. Parallel execution later = run each ready "level" concurrently — same model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.errors import ValidationError


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    config: dict[str, Any]


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    # Optional labelled output handle, used by branching nodes (e.g. condition
    # emits "true"/"false"). None = default flow.
    source_handle: str | None = None


@dataclass
class WorkflowGraph:
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    @classmethod
    def from_definition(cls, definition: dict[str, Any]) -> WorkflowGraph:
        nodes = [
            GraphNode(id=n["id"], type=n["type"], config=n.get("config", {}))
            for n in definition.get("nodes", [])
        ]
        edges = [
            GraphEdge(
                source=e["source"],
                target=e["target"],
                source_handle=e.get("source_handle"),
            )
            for e in definition.get("edges", [])
        ]
        graph = cls(nodes=nodes, edges=edges)
        graph.validate()
        return graph

    def node_map(self) -> dict[str, GraphNode]:
        return {n.id: n for n in self.nodes}

    def outgoing(self, node_id: str) -> list[GraphEdge]:
        return [e for e in self.edges if e.source == node_id]

    def validate(self) -> None:
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValidationError("Duplicate node ids in workflow")
        idset = set(ids)
        for e in self.edges:
            if e.source not in idset or e.target not in idset:
                raise ValidationError(f"Edge references unknown node: {e}")
        self.topological_order()  # raises on cycle

    def topological_order(self) -> list[str]:
        """Kahn's algorithm. Raises if the graph contains a cycle."""
        indegree = {n.id: 0 for n in self.nodes}
        for e in self.edges:
            indegree[e.target] += 1
        queue = [nid for nid, d in indegree.items() if d == 0]
        order: list[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for e in self.outgoing(nid):
                indegree[e.target] -= 1
                if indegree[e.target] == 0:
                    queue.append(e.target)
        if len(order) != len(self.nodes):
            raise ValidationError("Workflow contains a cycle")
        return order
