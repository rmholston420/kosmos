"""Ed25519 JWS signing over JCS canonical JSON (ADR-006, ADR-006a, ADR-032).

Pure-primitive module: no I/O orchestration beyond loading PEM key files.
Ported from Rigpa-LMS ``backend/src/rigpa/domains/governance/constitution/signing.py``
per ADR-032. Kept as a standalone module (rather than inlined into
``verifier.py``) because a future Synedrion amendment workflow (Phase 6.3)
will need to sign fresh constitution versions — this module is the shared
signing surface.

The constitution is human-authored as ``vNNNN.yaml`` and stored alongside a
JCS-canonicalized JSON copy (``vNNNN.json``) plus a detached Ed25519
signature (``vNNNN.sig``, base64url-encoded ASCII). All three artifacts
travel together and the canonical JSON is what gets signed and later
verified at boot.
"""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)


def canonicalize(data: dict[str, Any]) -> bytes:
    """Serialize ``data`` to JCS canonical JSON bytes (RFC 8785).

    Uses ``rfc8785`` (already a Kosmos dependency for DataPort §1.10). The
    result is UTF-8 JSON bytes suitable for Ed25519 signing.

    Args:
        data: Constitution payload as a Python dict (loaded from YAML).

    Returns:
        Canonical UTF-8 JSON bytes suitable for signing.
    """
    result = rfc8785.dumps(data)
    if isinstance(result, str):
        return result.encode("utf-8")
    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    raise TypeError(
        f"rfc8785.dumps returned unexpected type {type(result).__name__}"
    )


def sign(canonical_json: bytes, private_key: Ed25519PrivateKey) -> str:
    """Sign ``canonical_json`` with Ed25519 and return a base64url signature.

    Args:
        canonical_json: JCS canonical JSON bytes (see :func:`canonicalize`).
        private_key: Ed25519 private key loaded via :func:`load_private_key`.

    Returns:
        Detached signature, base64url-encoded ASCII string. Padding is
        preserved (no ``rstrip("=")``) so encode/decode round-trips exactly.
    """
    sig_bytes = private_key.sign(canonical_json)
    return base64.urlsafe_b64encode(sig_bytes).decode("ascii")


def verify(
    canonical_json: bytes, signature_b64: str, public_key: Ed25519PublicKey
) -> bool:
    """Verify a detached Ed25519 signature.

    Args:
        canonical_json: JCS canonical JSON bytes the signature was
            computed over.
        signature_b64: base64url-encoded signature string (as produced by
            :func:`sign`).
        public_key: Ed25519 public key loaded via :func:`load_public_key`.

    Returns:
        ``True`` on successful verification, ``False`` on signature
        mismatch or malformed base64. Never raises for verification
        failure — the boolean is the failure signal.
    """
    try:
        sig_bytes = base64.urlsafe_b64decode(signature_b64.encode("ascii"))
    except (ValueError, binascii.Error):
        return False
    try:
        public_key.verify(sig_bytes, canonical_json)
    except InvalidSignature:
        return False
    return True


def load_public_key(path: Path) -> Ed25519PublicKey:
    """Load an Ed25519 public key from a PEM file.

    Args:
        path: Filesystem path to a PEM-encoded ``SubjectPublicKeyInfo`` file.

    Returns:
        Parsed :class:`Ed25519PublicKey`.

    Raises:
        TypeError: If the PEM does not encode an Ed25519 public key.
    """
    raw = path.read_bytes()
    key = load_pem_public_key(raw)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError(
            f"Expected Ed25519 public key, got {type(key).__name__}"
        )
    return key


def load_private_key(
    path: Path, password: bytes | None = None
) -> Ed25519PrivateKey:
    """Load an Ed25519 private key from a PEM file.

    Args:
        path: Filesystem path to a PEM-encoded ``PrivateKeyInfo`` file.
        password: Optional passphrase if the PEM is encrypted.

    Returns:
        Parsed :class:`Ed25519PrivateKey`.

    Raises:
        TypeError: If the PEM does not encode an Ed25519 private key.
    """
    raw = path.read_bytes()
    key = load_pem_private_key(raw, password=password)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError(
            f"Expected Ed25519 private key, got {type(key).__name__}"
        )
    return key
