"""Integration-layer tests: webhook HMAC verification and credential vault."""

import hashlib
import hmac
import json

import pytest
from cryptography.fernet import Fernet

from app.core.security import decrypt_secret, encrypt_secret
from app.modules.integrations.oauth import verify_webhook_hmac
from app.modules.integrations.vault import CredentialVault


# ---------------------------------------------------------------------------
# Webhook HMAC
# ---------------------------------------------------------------------------

class TestWebhookHmac:
    def _make_sig(self, payload: bytes, secret: str) -> str:
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def test_valid_signature_passes(self):
        payload = b'{"event": "push"}'
        secret = "s3cr3t-webhook-key"
        sig = self._make_sig(payload, secret)
        assert verify_webhook_hmac(payload, sig, secret) is True

    def test_wrong_secret_fails(self):
        payload = b'{"event": "push"}'
        sig = self._make_sig(payload, "correct-secret")
        assert verify_webhook_hmac(payload, sig, "wrong-secret") is False

    def test_tampered_payload_fails(self):
        payload = b'{"event": "push"}'
        secret = "s3cr3t"
        sig = self._make_sig(payload, secret)
        tampered = b'{"event": "delete"}'
        assert verify_webhook_hmac(tampered, sig, secret) is False

    def test_missing_prefix_fails(self):
        payload = b'hello'
        secret = "s3cr3t"
        raw_hex = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        # No "sha256=" prefix
        assert verify_webhook_hmac(payload, raw_hex, secret) is False

    def test_empty_payload_valid_sig(self):
        payload = b""
        secret = "s3cr3t"
        sig = self._make_sig(payload, secret)
        assert verify_webhook_hmac(payload, sig, secret) is True


# ---------------------------------------------------------------------------
# Credential vault (in-memory stub using the real encrypt/decrypt)
# ---------------------------------------------------------------------------

class TestCredentialVault:
    """Tests the Fernet encrypt/decrypt round-trip used by CredentialVault."""

    def test_encrypt_decrypt_round_trip(self):
        key = Fernet.generate_key().decode()
        import os
        os.environ["ENCRYPTION_KEY"] = key

        creds = {"access_token": "tok_abc123", "refresh_token": "ref_xyz"}
        blob = encrypt_secret(json.dumps(creds))

        # Must not be plaintext
        assert "tok_abc123" not in blob

        recovered = json.loads(decrypt_secret(blob))
        assert recovered == creds

    def test_different_keys_cannot_decrypt(self):
        """Fernet tokens are bound to the key they were encrypted with."""
        from cryptography.fernet import Fernet as _F, InvalidToken

        key1 = _F.generate_key()
        key2 = _F.generate_key()

        blob = _F(key1).encrypt(b"secret-value")
        with pytest.raises(InvalidToken):
            _F(key2).decrypt(blob)

    def test_empty_string_round_trip(self):
        import os
        key = Fernet.generate_key().decode()
        os.environ["ENCRYPTION_KEY"] = key

        blob = encrypt_secret("")
        assert decrypt_secret(blob) == ""
