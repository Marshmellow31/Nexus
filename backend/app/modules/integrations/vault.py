"""Credential vault — encrypt/decrypt connection credentials.

All nodes reference a connection_id. The executor calls get_credentials(connection_id)
which does the DB lookup + Fernet decryption. Plaintext never persists.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, PermissionError
from app.core.security import decrypt_secret, encrypt_secret
from app.modules.integrations.models import Connection


class CredentialVault:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
        display_name: str,
        credentials: dict,
        metadata: dict | None = None,
    ) -> Connection:
        conn = Connection(
            user_id=user_id,
            provider=provider,
            display_name=display_name,
            encrypted_credentials=encrypt_secret(json.dumps(credentials)),
            metadata_=metadata,
        )
        self._session.add(conn)
        await self._session.flush()
        return conn

    async def get_credentials(
        self, connection_id: str, user_id: uuid.UUID
    ) -> dict:
        result = await self._session.execute(
            select(Connection).where(Connection.id == uuid.UUID(connection_id))
        )
        conn = result.scalar_one_or_none()
        if not conn:
            raise NotFoundError(f"Connection {connection_id} not found")
        if conn.user_id != user_id:
            raise PermissionError("Access denied to connection")
        return json.loads(decrypt_secret(conn.encrypted_credentials))

    async def list_for_user(self, user_id: uuid.UUID) -> list[Connection]:
        result = await self._session.execute(
            select(Connection).where(
                Connection.user_id == user_id, Connection.is_active == True  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def delete(self, connection_id: str, user_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(Connection).where(Connection.id == uuid.UUID(connection_id))
        )
        conn = result.scalar_one_or_none()
        if not conn:
            raise NotFoundError(f"Connection {connection_id} not found")
        if conn.user_id != user_id:
            raise PermissionError("Access denied to connection")
        await self._session.delete(conn)
        await self._session.flush()
