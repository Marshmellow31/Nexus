"""Service container injected into every node's ExecutionContext.

Keeps nodes decoupled from construction/config so they stay unit-testable: a test
passes a fake AIService or http client without touching a database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.ai.service import AIService


@dataclass
class NodeServices:
    ai: AIService
    http: Any  # httpx.AsyncClient in production; a stub in tests
    # Resolves a connection_id -> decrypted credentials dict (vault lookup).
    get_credentials: Any = None
