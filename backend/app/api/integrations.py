"""Integration routes: OAuth connect/callback, connection management, webhook triggers."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ConnectionOut
from app.core.config import settings
from app.core.db import get_session
from app.core.errors import AuthError, NotFoundError
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.integrations.oauth import PROVIDERS, oauth_manager
from app.modules.integrations.vault import CredentialVault

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ── Connection listing ────────────────────────────────────────────────────────

@router.get("/connections", response_model=list[ConnectionOut])
async def list_connections(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    vault = CredentialVault(session)
    return await vault.list_for_user(user.id)


@router.delete("/connections/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    vault = CredentialVault(session)
    await vault.delete(connection_id, user.id)


# ── OAuth flow ────────────────────────────────────────────────────────────────

@router.get("/connect/{provider}")
async def connect_provider(
    provider: str,
    user: User = Depends(get_current_user),
):
    """Redirect the user to the provider's OAuth consent screen."""
    redirect_uri = f"{settings.api_base_url}/api/integrations/callback/{provider}"
    url = oauth_manager.authorization_url(provider, str(user.id), redirect_uri)
    return RedirectResponse(url)


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    session: AsyncSession = Depends(get_session),
):
    """Exchange the auth code for tokens and store them encrypted."""
    redirect_uri = f"{settings.api_base_url}/api/integrations/callback/{provider}"
    user_id_str, credentials = await oauth_manager.exchange_code(
        provider, code, state, redirect_uri
    )

    vault = CredentialVault(session)
    prov_obj = PROVIDERS[provider]
    display_name = f"{prov_obj.name.title()} ({credentials.get('email', 'connected')})"
    await vault.store(
        user_id=uuid.UUID(user_id_str),
        provider=provider,
        display_name=display_name,
        credentials=credentials,
        metadata={"scopes": prov_obj.scopes},
    )

    # In production: redirect back to the frontend settings page
    return RedirectResponse(f"{settings.cors_origins[0]}/settings?connected={provider}")


# ── API-key connections (Notion, Linear, etc.) ───────────────────────────────

class ApiKeyConnectionRequest(BaseModel):
    provider: str   # e.g. "notion", "linear"
    api_key: str
    display_name: str | None = None


@router.post("/connect-key", response_model=ConnectionOut, status_code=201)
async def connect_api_key(
    body: ApiKeyConnectionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Store an API-key-based connection (Notion integration token, Linear API key, etc.)."""
    vault = CredentialVault(session)
    label = body.display_name or f"{body.provider.title()} (API key)"
    conn = await vault.store(
        user_id=user.id,
        provider=body.provider,
        display_name=label,
        credentials={"api_key": body.api_key},
        metadata={"method": "api_key"},
    )
    return conn


# ── Webhook trigger ───────────────────────────────────────────────────────────

class WebhookResponse(BaseModel):
    run_id: str
    status: str


@router.post("/webhooks/{workflow_id}/{secret}", response_model=WebhookResponse)
async def webhook_trigger(
    workflow_id: str,
    secret: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_hub_signature_256: str | None = Header(default=None),
):
    """Webhook trigger endpoint. Validates secret, enqueues run."""
    from sqlalchemy import select

    from app.modules.integrations.oauth import verify_webhook_hmac
    from app.modules.runs.service import RunService
    from app.modules.workflows.models import Workflow
    from app.modules.workflows.service import WorkflowService

    result = await session.execute(
        select(Workflow).where(Workflow.id == uuid.UUID(workflow_id))
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise NotFoundError(f"Workflow {workflow_id} not found")

    # Verify secret
    if wf.webhook_secret != secret:
        raise AuthError("Invalid webhook secret")

    # Optional HMAC verification (GitHub-style)
    if x_hub_signature_256 and wf.webhook_secret:
        body = await request.body()
        if not verify_webhook_hmac(body, x_hub_signature_256, wf.webhook_secret):
            raise AuthError("Webhook HMAC verification failed")

    payload = {}
    try:
        payload = await request.json()
    except Exception:
        pass

    run_svc = RunService(session)
    run = await run_svc.create(
        workflow_id=wf.id,
        user_id=wf.user_id,
        trigger_type="webhook",
        trigger_payload=payload,
        definition_snapshot=wf.definition,
    )

    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await pool.enqueue_job("execute_workflow", str(run.id))
        await pool.aclose()
    except Exception:
        pass

    return WebhookResponse(run_id=str(run.id), status="queued")
