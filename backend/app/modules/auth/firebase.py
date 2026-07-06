"""Firebase ID token verification. All Firebase contact is isolated in this file.

Dev bypass: when AUTH_DEV_BYPASS=true (local only), accept a header
  X-Dev-User-Id: <any-string>
instead of a real Firebase token. This keeps local dev dependency-free.

Real Firebase verification uses the Admin SDK (JWKS cached by the SDK itself).
"""

from __future__ import annotations

import json
from functools import lru_cache

from app.core.config import settings
from app.core.errors import AuthError


@lru_cache(maxsize=1)
def _firebase_app():
    import firebase_admin
    from firebase_admin import credentials

    if settings.firebase_credentials_json:
        cred = credentials.Certificate(json.loads(settings.firebase_credentials_json))
    elif settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        raise AuthError("Firebase credentials not configured")

    return firebase_admin.initialize_app(cred)


async def verify_firebase_token(token: str) -> dict:
    """Returns decoded token dict with uid, email, name."""
    if settings.auth_dev_bypass:
        raise AuthError("Dev bypass active — use X-Dev-User-Id header")

    try:
        from firebase_admin import auth

        _firebase_app()
        decoded = auth.verify_id_token(token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name") or decoded.get("display_name"),
        }
    except Exception as exc:
        raise AuthError(f"Invalid Firebase token: {exc}") from exc
