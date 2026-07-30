"""Constitution signature verifier facade.

Thin wrapper over :mod:`plugins.praxis.constitution.signing` that binds a
public key location (default: co-located ``pubkey.pem`` under
``governance/constitution/``) to a stateless verification call. Ported from
Rigpa-LMS ``backend/src/rigpa/domains/governance/constitution/verifier.py``
per ADR-032, adapted for Kosmos's ``governance/constitution/`` artifact
layout.
"""

from __future__ import annotations

from pathlib import Path

from plugins.praxis.constitution.errors import (
    ConstitutionMalformedError,
    ConstitutionNotFoundError,
)
from plugins.praxis.constitution.signing import load_public_key, verify


_DEFAULT_PUBKEY_PATH = (
    Path(__file__).resolve().parents[3]
    / "governance"
    / "constitution"
    / "pubkey.pem"
)


class ConstitutionVerifier:
    """Verify Ed25519 signatures against a configured public key.

    The verifier is stateless-per-call: the public key is reloaded on each
    :meth:`verify` invocation. That is intentional — boot-time verification
    happens exactly once, and the cost of one PEM parse is negligible next
    to the security benefit of always reading the currently on-disk key.
    """

    def __init__(self, pubkey_path: Path | None = None) -> None:
        """Construct a verifier bound to a public key path.

        Args:
            pubkey_path: PEM public-key path. If omitted, defaults to
                ``governance/constitution/pubkey.pem`` relative to the
                Kosmos monorepo root.
        """
        self.pubkey_path = pubkey_path or _DEFAULT_PUBKEY_PATH

    def verify(self, canonical_json: bytes, signature_b64: str) -> bool:
        """Verify a signature against the configured pubkey.

        Args:
            canonical_json: JCS canonical JSON bytes over which the
                signature was computed.
            signature_b64: Detached signature as base64url-encoded ASCII.

        Returns:
            ``True`` on successful verification, ``False`` on any
            signature mismatch or malformed input. Never raises for a
            verification failure — the boolean is the failure signal.

        Raises:
            ConstitutionNotFoundError: If the pubkey file is missing.
            ConstitutionMalformedError: If the pubkey file exists but is
                not a valid Ed25519 PEM.
        """
        if not self.pubkey_path.exists():
            raise ConstitutionNotFoundError(
                f"Constitution public key not found at {self.pubkey_path}"
            )
        try:
            public_key = load_public_key(self.pubkey_path)
        except (ValueError, TypeError) as exc:
            raise ConstitutionMalformedError(
                f"Constitution public key at {self.pubkey_path} is not a "
                f"valid Ed25519 PEM: {exc}"
            ) from exc

        return verify(canonical_json, signature_b64, public_key)
