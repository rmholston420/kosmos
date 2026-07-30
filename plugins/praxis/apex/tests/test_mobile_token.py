"""Contract tests for the SecretsPort-backed mobile signed-token service.

ADR-033 Q1=C · spec §17.13 · Ed25519 24h TTL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

from plugins.praxis.apex import (
    MOBILE_TOKEN_SIGNING_KEY,
    MobileTokenService,
    TokenExpiredError,
    TokenMalformedError,
    TokenTamperError,
)
from ports.secrets import SecretValue


# ---------------------------------------------------------------------------
# Fixtures + fake SecretsPort
# ---------------------------------------------------------------------------


class _FakeSecretsPort:
    """Serves a single key from an in-memory dict. Async parity with the port."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = dict(secrets)
        self.get_calls: list[str] = []

    async def get_secret(self, key: str) -> SecretValue:
        self.get_calls.append(key)
        if key not in self._secrets:
            raise KeyError(key)
        return SecretValue(self._secrets[key])


def _ed25519_pem() -> str:
    key = Ed25519PrivateKey.generate()
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@pytest.fixture
def secrets_pem():
    return _ed25519_pem()


@pytest.fixture
def clock():
    base = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    state = {"now": base}

    def _clock() -> datetime:
        return state["now"]

    _clock.set = lambda t: state.__setitem__("now", t)  # type: ignore[attr-defined]
    _clock.advance = lambda d: state.__setitem__(  # type: ignore[attr-defined]
        "now", state["now"] + d
    )
    _clock.base = base  # type: ignore[attr-defined]
    return _clock


@pytest.fixture
def service(secrets_pem, clock):
    port = _FakeSecretsPort({MOBILE_TOKEN_SIGNING_KEY: secrets_pem})
    return MobileTokenService(port, clock=clock)


# ---------------------------------------------------------------------------
# Roundtrip
# ---------------------------------------------------------------------------


class TestMobileTokenRoundtrip:
    async def test_mint_verify_roundtrip(self, service):
        token = await service.mint_token("approval-1", "approve")
        verified = await service.verify_token(token)
        assert verified.approval_id == "approval-1"
        assert verified.action == "approve"

    async def test_mint_verify_reject_action(self, service):
        token = await service.mint_token("approval-2", "reject")
        verified = await service.verify_token(token)
        assert verified.action == "reject"

    async def test_mint_produces_two_b64url_segments(self, service):
        token = await service.mint_token("approval-1", "approve")
        parts = token.split(".")
        assert len(parts) == 2
        assert all(parts)  # both non-empty

    async def test_verify_returns_exp_at_mint_plus_24h(self, service, clock):
        token = await service.mint_token("approval-1", "approve")
        verified = await service.verify_token(token)
        expected = clock.base + timedelta(hours=24)
        # Microsecond precision preserved through roundtrip.
        assert verified.exp == expected


# ---------------------------------------------------------------------------
# Expiry
# ---------------------------------------------------------------------------


class TestMobileTokenExpiry:
    async def test_expired_token_raises(self, service, clock):
        token = await service.mint_token("approval-1", "approve")
        clock.advance(timedelta(hours=24, seconds=1))
        with pytest.raises(TokenExpiredError):
            await service.verify_token(token)

    async def test_token_valid_up_to_ttl_boundary(self, service, clock):
        token = await service.mint_token("approval-1", "approve")
        clock.advance(timedelta(hours=24) - timedelta(microseconds=1))
        # Still valid at t = mint + 24h - 1us.
        verified = await service.verify_token(token)
        assert verified.approval_id == "approval-1"


# ---------------------------------------------------------------------------
# Tamper
# ---------------------------------------------------------------------------


class TestMobileTokenTamper:
    async def test_flipped_signature_bit_raises_tamper(self, service):
        token = await service.mint_token("approval-1", "approve")
        payload_b64, _, sig_b64 = token.partition(".")
        # Reverse the signature — guaranteed to invalidate for any Ed25519 sig.
        tampered = f"{payload_b64}.{sig_b64[::-1]}"
        with pytest.raises(TokenTamperError):
            await service.verify_token(tampered)

    async def test_flipped_payload_bit_raises_tamper(self, service):
        token = await service.mint_token("approval-1", "approve")
        payload_b64, _, sig_b64 = token.partition(".")
        # Prepend an extra byte to shift payload — guarantees mismatch.
        tampered_payload = "AA" + payload_b64
        tampered = f"{tampered_payload}.{sig_b64}"
        with pytest.raises((TokenTamperError, TokenMalformedError)):
            await service.verify_token(tampered)

    async def test_swapped_signature_across_two_tokens_raises_tamper(
        self, service
    ):
        token_a = await service.mint_token("approval-a", "approve")
        token_b = await service.mint_token("approval-b", "reject")
        payload_a, _, _ = token_a.partition(".")
        _, _, sig_b = token_b.partition(".")
        swapped = f"{payload_a}.{sig_b}"
        with pytest.raises(TokenTamperError):
            await service.verify_token(swapped)


# ---------------------------------------------------------------------------
# Malformed
# ---------------------------------------------------------------------------


class TestMobileTokenMalformed:
    async def test_empty_token_raises_malformed(self, service):
        with pytest.raises(TokenMalformedError):
            await service.verify_token("")

    async def test_missing_dot_separator_raises_malformed(self, service):
        with pytest.raises(TokenMalformedError):
            await service.verify_token("no-dot-here")

    async def test_empty_payload_raises_malformed(self, service):
        with pytest.raises(TokenMalformedError):
            await service.verify_token(".signature")

    async def test_empty_signature_raises_malformed(self, service):
        with pytest.raises(TokenMalformedError):
            await service.verify_token("payload.")

    async def test_bad_base64_or_bad_signature_raises(self, service):
        # Non-base64 or unsigned payload should raise either malformed
        # (parse failure) or tamper (signature verify failure). Both are
        # acceptable — signature verify runs after b64 decode.
        with pytest.raises((TokenMalformedError, TokenTamperError)):
            await service.verify_token("!!!invalid-b64!!!.zzz")

    async def test_invalid_action_at_mint_raises_malformed(self, service):
        with pytest.raises(TokenMalformedError):
            await service.mint_token("approval-1", "sudo-approve")

    async def test_empty_approval_id_at_mint_raises_malformed(self, service):
        with pytest.raises(TokenMalformedError):
            await service.mint_token("   ", "approve")


# ---------------------------------------------------------------------------
# Non-Ed25519 key rejected
# ---------------------------------------------------------------------------


class TestMobileTokenNonEd25519Key:
    async def test_rsa_key_rejected(self, clock):
        rsa_key = generate_private_key(public_exponent=65537, key_size=2048)
        rsa_pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        port = _FakeSecretsPort({MOBILE_TOKEN_SIGNING_KEY: rsa_pem})
        svc = MobileTokenService(port, clock=clock)
        with pytest.raises(TokenMalformedError, match="not Ed25519"):
            await svc.mint_token("approval-1", "approve")

    async def test_garbage_key_rejected(self, clock):
        port = _FakeSecretsPort({MOBILE_TOKEN_SIGNING_KEY: "not-a-pem-key"})
        svc = MobileTokenService(port, clock=clock)
        with pytest.raises(TokenMalformedError, match="failed to parse as PEM"):
            await svc.mint_token("approval-1", "approve")
