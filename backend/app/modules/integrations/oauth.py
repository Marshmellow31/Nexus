"""OAuth flow manager.

Handles the authorization URL generation and code-exchange for Google and GitHub.
Tokens are stored encrypted via CredentialVault after exchange.

Design: each provider is a small dataclass. Adding a provider = one entry here.
The frontend redirects the user to /api/integrations/connect/{provider}, the user
authorises, the provider redirects to /api/integrations/callback/{provider}, and
we exchange + store the token. State param prevents CSRF.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.errors import AuthError, ValidationError


@dataclass(frozen=True)
class OAuthProvider:
    name: str
    auth_url: str
    token_url: str
    client_id_setting: str
    client_secret_setting: str
    scopes: list[str]


PROVIDERS: dict[str, OAuthProvider] = {
    "google": OAuthProvider(
        name="google",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        client_id_setting="google_client_id",
        client_secret_setting="google_client_secret",
        scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar.events",
            "openid",
            "email",
        ],
    ),
    "github": OAuthProvider(
        name="github",
        auth_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        client_id_setting="github_client_id",
        client_secret_setting="github_client_secret",
        scopes=["repo", "read:user"],
    ),
}


class OAuthManager:
    def __init__(self) -> None:
        self._state_store: dict[str, dict] = {}  # in-memory; use Redis in prod

    def get_provider(self, name: str) -> OAuthProvider:
        if name not in PROVIDERS:
            raise ValidationError(f"Unknown OAuth provider: {name}")
        return PROVIDERS[name]

    def authorization_url(self, provider_name: str, user_id: str, redirect_uri: str) -> str:
        provider = self.get_provider(provider_name)
        state = secrets.token_urlsafe(32)
        # Store state with 10-minute TTL metadata
        self._state_store[state] = {
            "user_id": user_id,
            "provider": provider_name,
            "expires": time.time() + 600,
        }
        params = {
            "client_id": self._client_id(provider),
            "redirect_uri": redirect_uri,
            "scope": " ".join(provider.scopes),
            "response_type": "code",
            "state": state,
            "access_type": "offline",  # Google: get refresh token
            "prompt": "consent",
        }
        return f"{provider.auth_url}?{urlencode(params)}"

    async def exchange_code(
        self, provider_name: str, code: str, state: str, redirect_uri: str
    ) -> tuple[str, dict]:
        """Returns (user_id, credentials_dict)."""
        meta = self._state_store.pop(state, None)
        if not meta or meta["expires"] < time.time():
            raise AuthError("Invalid or expired OAuth state")
        if meta["provider"] != provider_name:
            raise AuthError("OAuth state provider mismatch")

        provider = self.get_provider(provider_name)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                provider.token_url,
                data={
                    "client_id": self._client_id(provider),
                    "client_secret": self._client_secret(provider),
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            token_data = resp.json()

        if "error" in token_data:
            raise AuthError(f"OAuth exchange failed: {token_data['error']}")

        return meta["user_id"], token_data

    def _client_id(self, provider: OAuthProvider) -> str:
        val = getattr(settings, provider.client_id_setting, "")
        if not val:
            raise ValidationError(
                f"{provider.name} OAuth not configured (missing {provider.client_id_setting})"
            )
        return val

    def _client_secret(self, provider: OAuthProvider) -> str:
        val = getattr(settings, provider.client_secret_setting, "")
        if not val:
            raise ValidationError(
                f"{provider.name} OAuth not configured (missing {provider.client_secret_setting})"
            )
        return val


def verify_webhook_hmac(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub-style HMAC-SHA256 webhook signature."""
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


oauth_manager = OAuthManager()
