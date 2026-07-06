"""User model. Firebase owns credentials; we own profile + settings."""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Stub for future RBAC — single role string is enough for MVP
    role: Mapped[str] = mapped_column(String(32), default="user")

    workflows: Mapped[list["Workflow"]] = relationship(back_populates="user", lazy="noload")  # noqa: F821
    connections: Mapped[list["Connection"]] = relationship(back_populates="user", lazy="noload")  # noqa: F821
