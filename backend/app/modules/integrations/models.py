"""Connection model — stores encrypted OAuth tokens and user API keys.

Credentials are NEVER in workflow JSON. Nodes reference connection_id;
the engine resolves the actual secret server-side at execution time.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class Connection(Base, TimestampMixin):
    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Provider slug: "google", "github", "openai", "custom"
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Fernet-encrypted JSON blob: {"access_token": "...", "refresh_token": "...", ...}
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    # Non-sensitive metadata (scopes granted, token expiry, account email)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    user: Mapped["User"] = relationship(back_populates="connections")  # noqa: F821


class StoredItem(Base, TimestampMixin):
    """Lightweight storage for the action.store node — Nexus's internal 'notes'."""

    __tablename__ = "stored_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    collection: Mapped[str] = mapped_column(String(128), default="notes")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSONB)
