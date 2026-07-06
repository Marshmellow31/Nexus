"""Pydantic response/request schemas for the API layer.

Kept in one file while small. Split into per-module files when this grows past ~200 lines.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Auth / User ──────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Workflows ─────────────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger_type: str = "manual"
    definition: dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": []})


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    definition: dict[str, Any] | None = None
    is_active: bool | None = None


class WorkflowOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    trigger_type: str
    definition: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Runs ──────────────────────────────────────────────────────────────────────

class RunTrigger(BaseModel):
    trigger_payload: dict[str, Any] | None = None


class RunStepOut(BaseModel):
    id: uuid.UUID
    node_id: str
    node_type: str
    status: str
    output: dict[str, Any] | None
    error: str | None
    attempts: int
    duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_type: str
    trigger_payload: dict[str, Any] | None
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    steps: list[RunStepOut] = []

    model_config = {"from_attributes": True}


class RunSummaryOut(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_type: str
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Connections ───────────────────────────────────────────────────────────────

class ConnectionOut(BaseModel):
    id: uuid.UUID
    provider: str
    display_name: str
    is_active: bool
    metadata_: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
