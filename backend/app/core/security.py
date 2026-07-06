"""Credential encryption (Fernet) + SSRF-safe URL validation.

The vault stores OAuth tokens and user API keys encrypted at rest. Plaintext must
never touch the DB, logs, or API responses.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.errors import ValidationError


def _fernet() -> Fernet:
    key = settings.encryption_key.encode()
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:  # pragma: no cover - corruption/rotation
        raise ValidationError("Unable to decrypt stored credential") from exc


# --- SSRF guard for the HTTP node ---------------------------------------------

_BLOCKED_SCHEMES_MSG = "Only http/https URLs are allowed"


def _is_public_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_url_is_safe(url: str) -> None:
    """Raise ValidationError if the URL could target internal infrastructure.

    Resolves DNS and checks every resolved IP so DNS-rebinding / metadata-endpoint
    tricks (169.254.169.254, localhost, 10.x, etc.) are blocked.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(_BLOCKED_SCHEMES_MSG)
    host = parsed.hostname
    if not host:
        raise ValidationError("URL is missing a host")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValidationError(f"Could not resolve host: {host}") from exc

    for info in infos:
        ip_str = info[4][0]
        if not _is_public_ip(ip_str):
            raise ValidationError(
                f"Request to non-public address is blocked: {host} -> {ip_str}"
            )
