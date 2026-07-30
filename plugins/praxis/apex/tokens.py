"""Mobile signed-token service (ADR-033 Q1=C · spec §17.13).

Ed25519-signed one-tap approve/reject tokens with 24h TTL for
SMS/ntfy mobile fallback.

Token wire format (JCS canonical JSON + base64url):

    base64url(
        canonical_json({
            "approval_id": "<uuid>",
            "action": "approve" | "reject",
            "exp": "<UTC ISO8601 with 'Z' suffix>",
        })
    )
    "."
    base64url(ed25519_signature)

Signing key retrieved via SecretsPort under the logical name
``apex.approval.mobile_token.signing_key`` (Restricted tier per §17.13).
The port returns a ``SecretValue`` — ``.reveal()`` is the sole plaintext
access point. Every call to ``mint_token`` or ``verify_token`` calls
``.reveal()`` once and drops the raw key immediately.

The signing key is stored PEM-encoded (unencrypted, but wrapped by the
age-file backend). ``SecretsPort.put_secret(...)`` accepts the raw PEM
string.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from plugins.praxis.apex.errors import (
    TokenExpiredError,
    TokenMalformedError,
    TokenTamperError,
)

__all__ = [
    "MOBILE_TOKEN_SIGNING_KEY",
    "MobileTokenService",
    "VerifiedTokenAction",
    "b64url_decode",
    "b64url_encode",
]


MOBILE_TOKEN_SIGNING_KEY = "apex.approval.mobile_token.signing_key"
"""SecretsPort logical name for the Ed25519 signing key (PEM PKCS8)."""

MOBILE_TOKEN_TTL = timedelta(hours=24)
"""24h TTL per spec §17.13."""

_VALID_ACTIONS = frozenset({"approve", "reject"})


@dataclass(frozen=True, slots=True)
class VerifiedTokenAction:
    """Result of :meth:`MobileTokenService.verify_token`.

    ``exp`` is preserved so callers can log token freshness.
    """

    approval_id: str
    action: str  # "approve" | "reject"
    exp: datetime


# ---------------------------------------------------------------------------
# base64url helpers (unpadded, per RFC 7515)
# ---------------------------------------------------------------------------


def b64url_encode(raw: bytes) -> str:
    """URL-safe base64 without padding (RFC 7515 §2)."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64url_decode(encoded: str) -> bytes:
    """Inverse of :func:`b64url_encode`. Pads before decode."""
    pad = 4 - (len(encoded) % 4)
    if pad != 4:
        encoded = encoded + ("=" * pad)
    return base64.urlsafe_b64decode(encoded.encode("ascii"))


# ---------------------------------------------------------------------------
# MobileTokenService
# ---------------------------------------------------------------------------


class MobileTokenService:
    """Mint and verify mobile approve/reject tokens (ADR-033 Q1=C).

    Stateless. Every call reads the signing key from SecretsPort under
    :data:`MOBILE_TOKEN_SIGNING_KEY`. The port's ``SecretValue`` wrapper
    keeps the key redacted in logs and repr; ``.reveal()`` is called
    once per operation.
    """

    def __init__(self, secrets_port: Any, *, clock: Any = None) -> None:
        """Wire a SecretsPort.

        ``secrets_port`` must have an async ``get_secret(key: str) ->
        SecretValue`` verb (per ADR-024).

        ``clock`` is an optional callable returning ``datetime`` (UTC).
        Tests pass a fake clock to freeze time; production defaults to
        :func:`datetime.now(timezone.utc)`.
        """
        self._secrets = secrets_port
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def _load_private_key(self) -> Ed25519PrivateKey:
        secret_value = await self._secrets.get_secret(MOBILE_TOKEN_SIGNING_KEY)
        pem = secret_value.reveal()
        try:
            key = serialization.load_pem_private_key(
                pem.encode("utf-8"), password=None
            )
        except Exception as exc:
            raise TokenMalformedError(
                f"mobile-token signing key at {MOBILE_TOKEN_SIGNING_KEY!r} "
                f"failed to parse as PEM PKCS8: {exc}"
            ) from exc
        if not isinstance(key, Ed25519PrivateKey):
            raise TokenMalformedError(
                f"mobile-token signing key at {MOBILE_TOKEN_SIGNING_KEY!r} "
                f"is not Ed25519 (got {type(key).__name__})"
            )
        return key

    async def _load_public_key(self) -> Ed25519PublicKey:
        private = await self._load_private_key()
        return private.public_key()

    async def mint_token(self, approval_id: str, action: str) -> str:
        """Return a base64url-encoded signed token.

        ``action`` MUST be ``"approve"`` or ``"reject"``.
        """
        if action not in _VALID_ACTIONS:
            raise TokenMalformedError(
                f"action must be one of {sorted(_VALID_ACTIONS)!r}, got {action!r}"
            )
        if not approval_id or not approval_id.strip():
            raise TokenMalformedError("approval_id must be non-empty")
        exp = self._clock() + MOBILE_TOKEN_TTL
        payload: Mapping[str, Any] = {
            "approval_id": approval_id,
            "action": action,
            "exp": _to_iso_utc(exp),
        }
        canonical = rfc8785.dumps(payload)
        key = await self._load_private_key()
        signature = key.sign(canonical)
        return f"{b64url_encode(canonical)}.{b64url_encode(signature)}"

    async def verify_token(self, token: str) -> VerifiedTokenAction:
        """Return :class:`VerifiedTokenAction` on success.

        Raises:
            :class:`TokenMalformedError` — token cannot be parsed.
            :class:`TokenTamperError` — signature fails verification.
            :class:`TokenExpiredError` — ``exp`` is in the past.
        """
        if not token or "." not in token:
            raise TokenMalformedError(
                "token must be '<b64url-payload>.<b64url-signature>'"
            )
        payload_b64, _, sig_b64 = token.partition(".")
        if not payload_b64 or not sig_b64:
            raise TokenMalformedError(
                "token payload and signature must both be non-empty"
            )
        try:
            canonical = b64url_decode(payload_b64)
            signature = b64url_decode(sig_b64)
        except Exception as exc:
            raise TokenMalformedError(
                f"token base64url decode failed: {exc}"
            ) from exc

        # Verify signature BEFORE parsing payload — tamper-first check
        # prevents leaking payload structure to unauthenticated callers.
        pubkey = await self._load_public_key()
        try:
            pubkey.verify(signature, canonical)
        except InvalidSignature as exc:
            raise TokenTamperError(
                "token signature failed Ed25519 verification"
            ) from exc

        try:
            import json

            payload = json.loads(canonical.decode("utf-8"))
        except Exception as exc:
            raise TokenMalformedError(
                f"token payload failed JSON parse after signature verify: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise TokenMalformedError(
                f"token payload must be a JSON object, got {type(payload).__name__}"
            )
        approval_id = payload.get("approval_id")
        action = payload.get("action")
        exp_str = payload.get("exp")
        if (
            not isinstance(approval_id, str)
            or not isinstance(action, str)
            or not isinstance(exp_str, str)
        ):
            raise TokenMalformedError(
                "token payload must have string approval_id, action, exp"
            )
        if action not in _VALID_ACTIONS:
            raise TokenMalformedError(
                f"token action must be one of {sorted(_VALID_ACTIONS)!r}, "
                f"got {action!r}"
            )
        try:
            exp = _from_iso_utc(exp_str)
        except Exception as exc:
            raise TokenMalformedError(
                f"token exp must be ISO8601 UTC with 'Z' suffix, got {exp_str!r}: {exc}"
            ) from exc
        now = self._clock()
        if exp < now:
            raise TokenExpiredError(
                f"token exp {exp.isoformat()} is before now {now.isoformat()}"
            )
        return VerifiedTokenAction(
            approval_id=approval_id, action=action, exp=exp
        )


# ---------------------------------------------------------------------------
# ISO8601 helpers — spec §17.13 tokens use 'Z' suffix, not '+00:00'
# ---------------------------------------------------------------------------


def _to_iso_utc(dt: datetime) -> str:
    """UTC-Z ISO8601 (microsecond precision, trailing 'Z')."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=None).isoformat(timespec="microseconds") + "Z"


def _from_iso_utc(s: str) -> datetime:
    """Inverse of :func:`_to_iso_utc`. Strict about 'Z' suffix."""
    if not s.endswith("Z"):
        raise ValueError(f"expected 'Z' suffix, got {s!r}")
    return datetime.fromisoformat(s[:-1]).replace(tzinfo=timezone.utc)
