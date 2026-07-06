"""Run and RunStep models — execution history + run inspector data."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class Run(Base, TimestampMixin):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "pending" | "running" | "succeeded" | "failed" | "cancelled"
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), default="manual")
    trigger_payload: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    # Snapshot of workflow definition at execution time (immutable history)
    definition_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    workflow: Mapped["Workflow"] = relationship(back_populates="runs")  # noqa: F821
    steps: Mapped[list["RunStep"]] = relationship(
        back_populates="run", lazy="noload", order_by="RunStep.created_at"
    )


class RunStep(Base, TimestampMixin):
    __tablename__ = "run_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_id: Mapped[str] = mapped_column(String(128), nullable=False)
    node_type: Mapped[str] = mapped_column(String(128), nullable=False)
    # "running" | "succeeded" | "failed" | "skipped"
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    input_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    output: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    run: Mapped["Run"] = relationship(back_populates="steps")
