"""Workflow and related models."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # "manual" | "webhook" | "schedule" — schedule/webhook wired in later phases
    trigger_type: Mapped[str] = mapped_column(String(32), default="manual")
    # Webhook secret for trigger_type=webhook
    webhook_secret: Mapped[str | None] = mapped_column(String(64))
    # DAG definition: { nodes: [...], edges: [...] }
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Version counter for optimistic locking / history (future)
    version: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["User"] = relationship(back_populates="workflows")  # noqa: F821
    runs: Mapped[list["Run"]] = relationship(back_populates="workflow", lazy="noload")  # noqa: F821
