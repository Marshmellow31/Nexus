"""FastAPI auth dependencies.

`get_current_user` is the single auth gate for all protected routes.
It provisions the user row on first sign-in (upsert by firebase_uid).
"""

from __future__ import annotations

import uuid

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.errors import AuthError
from app.modules.auth.firebase import verify_firebase_token
from app.modules.auth.models import User


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_dev_user_id: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    # --- Dev bypass (local only) ------------------------------------------------
    if settings.auth_dev_bypass:
        uid = x_dev_user_id or "dev-user-001"
        return await _upsert_user(
            session,
            firebase_uid=uid,
            email=f"{uid}@dev.local",
            display_name="Dev User",
        )

    # --- Real Firebase verification ---------------------------------------------
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing Authorization header")
    token = authorization.removeprefix("Bearer ")
    decoded = await verify_firebase_token(token)
    return await _upsert_user(
        session,
        firebase_uid=decoded["uid"],
        email=decoded.get("email", ""),
        display_name=decoded.get("name"),
    )


async def _upsert_user(
    session: AsyncSession,
    *,
    firebase_uid: str,
    email: str,
    display_name: str | None,
) -> User:
    result = await session.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
        )
        session.add(user)
        await session.flush()
    return user
