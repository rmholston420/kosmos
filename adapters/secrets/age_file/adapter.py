"""AgeFileSecretsAdapter — SecretsPort backed by an age-encrypted YAML file.

ADR-024: primary Kosmos SecretsPort adapter. Local-first, no daemon, no
network. Rotates by atomically re-encrypting the entire secrets file.

Design notes
------------
- ``pyrage`` and ``yaml`` are imported **lazily** inside ``PyrageBackend``
  so unit tests using ``InMemoryAgeBackend`` do not require either
  dependency installed. This mirrors the Stage 1.4 pattern of a lazy
  ``redis`` import in ``ValkeyEventBusAdapter``.
- ``AgeBackend`` is a small ``Protocol`` isolating the two operations the
  adapter needs from age (``decrypt`` + ``encrypt``). Real crypto and
  in-memory fakes both satisfy it — contract tests exercise the fake, and
  a live-decrypt smoke test is possible on Colossus by DI'ing
  ``PyrageBackend``.
- Rotation writes to a sibling temp file then ``os.replace`` — atomic on
  POSIX so a crash mid-rotate cannot corrupt ``secrets.age``.
- The full plaintext YAML is held in memory only inside a method call
  frame; the adapter never caches it as an attribute.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ports.secrets import SecretValue, SecretsPort

__all__ = [
    "AgeBackend",
    "PyrageBackend",
    "InMemoryAgeBackend",
    "AgeFileSecretsAdapter",
    "get_age_file_secrets_adapter",
]


# ----------------------------------------------------------------------
# AgeBackend Protocol — isolates age crypto so tests can inject a fake
# ----------------------------------------------------------------------


@runtime_checkable
class AgeBackend(Protocol):
    """Minimal age crypto surface used by AgeFileSecretsAdapter."""

    def decrypt(self, ciphertext: bytes) -> bytes: ...

    def encrypt(self, plaintext: bytes) -> bytes: ...


# ----------------------------------------------------------------------
# PyrageBackend — real crypto. Lazy imports so tests need not install pyrage
# ----------------------------------------------------------------------


class PyrageBackend:
    """Real age crypto via ``pyrage`` (Apache-2.0 / MIT).

    Recipients are derived from the identity file's public key so that
    rotation writes are decryptable by the same identity. Multi-recipient
    (e.g., succession key escrow — spec §7 digital-estate succession) is
    a future extension.
    """

    def __init__(self, identity_path: Path) -> None:
        self._identity_path = identity_path
        self._identity: Any | None = None
        self._recipient: Any | None = None

    def _ensure_identity(self) -> None:
        if self._identity is not None:
            return
        import pyrage  # lazy

        raw = self._identity_path.read_text(encoding="utf-8")
        secret_key = self._extract_secret_key(raw)
        self._identity = pyrage.x25519.Identity.from_str(secret_key)
        # Public key -> recipient for encrypt round-trip
        self._recipient = self._identity.to_public()

    @staticmethod
    def _extract_secret_key(raw: str) -> str:
        """Return the AGE-SECRET-KEY line from an identity file.

        ``age-keygen -o path`` writes a multi-line file:

            # created: 2026-07-29T...
            # public key: age1...
            AGE-SECRET-KEY-1...

        ``pyrage.x25519.Identity.from_str`` wants the Bech32 secret only.
        This helper strips comments and blank lines and returns the
        single secret-key line. Raises ``ValueError`` if none is found
        so a bad identity file fails loudly at first use rather than
        surfacing as an opaque ``IdentityError: invalid Bech32 encoding``.
        """
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("AGE-SECRET-KEY-"):
                return stripped
        raise ValueError(
            "identity file does not contain an AGE-SECRET-KEY- line; "
            "generate one with 'age-keygen -o <path>' or pass the raw "
            "Bech32 secret string in the file."
        )

    def decrypt(self, ciphertext: bytes) -> bytes:
        import pyrage  # lazy

        self._ensure_identity()
        assert self._identity is not None
        return pyrage.decrypt(ciphertext, [self._identity])

    def encrypt(self, plaintext: bytes) -> bytes:
        import pyrage  # lazy

        self._ensure_identity()
        assert self._recipient is not None
        return pyrage.encrypt(plaintext, [self._recipient])


# ----------------------------------------------------------------------
# InMemoryAgeBackend — deterministic fake for contract tests
# ----------------------------------------------------------------------


@dataclass
class InMemoryAgeBackend:
    """No-op 'crypto': encrypt/decrypt round-trip through a byte prefix.

    Contract tests use this to exercise the adapter without requiring
    ``pyrage`` or a real identity. The prefix (``b"AGE-FAKE:"``) makes it
    obvious in a hex dump that this is not real ciphertext.
    """

    prefix: bytes = b"AGE-FAKE:"
    decrypt_should_fail: bool = False

    def decrypt(self, ciphertext: bytes) -> bytes:
        if self.decrypt_should_fail:
            raise RuntimeError("simulated decrypt failure")
        if not ciphertext.startswith(self.prefix):
            raise ValueError("InMemoryAgeBackend: ciphertext missing sentinel prefix")
        return ciphertext[len(self.prefix) :]

    def encrypt(self, plaintext: bytes) -> bytes:
        return self.prefix + plaintext


# ----------------------------------------------------------------------
# AgeFileSecretsAdapter — SecretsPort satisfier
# ----------------------------------------------------------------------


class AgeFileSecretsAdapter:
    """SecretsPort backed by a local age-encrypted YAML file (ADR-024).

    Environment variables:
      KOSMOS_SECRETS_PATH        - path to secrets.age
                                   (default: ~/.kosmos/secrets/secrets.age)
      KOSMOS_AGE_IDENTITY_PATH   - path to age identity file (required
                                   when using PyrageBackend; irrelevant
                                   when a backend is DI'd in)
    """

    def __init__(
        self,
        *,
        secrets_path: Path,
        backend: AgeBackend,
    ) -> None:
        self._secrets_path = secrets_path
        self._backend = backend
        self._closed = False
        # A single asyncio.Lock serializes rotate/put to prevent
        # interleaved re-encrypts from corrupting the file. Reads are
        # cheap and also grab it so a rotate cannot land mid-decrypt.
        self._lock = asyncio.Lock()

    # --- SecretsPort surface -------------------------------------------------

    async def get_secret(self, key: str) -> SecretValue:
        async with self._lock:
            mapping = self._load_mapping_or_empty()
        if key not in mapping:
            raise KeyError(f"secret not found: {key!r}")
        raw = mapping[key]
        if not isinstance(raw, str):
            raise TypeError(
                f"secret {key!r} has non-string value of type {type(raw).__name__}; "
                "AgeFileSecretsAdapter stores string values only"
            )
        return SecretValue(raw)

    async def put_secret(self, key: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("secret value must be str")
        async with self._lock:
            mapping = self._load_mapping_or_empty()
            mapping[key] = value
            self._write_mapping_atomic(mapping)

    async def rotate(self, key: str, new_value: str) -> None:
        if not isinstance(new_value, str):
            raise TypeError("rotated secret value must be str")
        async with self._lock:
            mapping = self._load_mapping_or_empty()
            if key not in mapping:
                raise KeyError(
                    f"cannot rotate unknown secret {key!r}; "
                    "use put_secret to create it first"
                )
            mapping[key] = new_value
            self._write_mapping_atomic(mapping)

    async def is_healthy(self) -> bool:
        # Non-throwing per ADR-023 rule 5 (pattern reused for all ports).
        try:
            async with self._lock:
                self._load_mapping_or_empty()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        # Idempotent: no resources to release; mark closed for tests.
        self._closed = True

    # --- internals -----------------------------------------------------------

    def _load_mapping_or_empty(self) -> dict[str, Any]:
        """Decrypt the secrets file into a mutable dict.

        A missing file is treated as an empty mapping so put_secret can
        bootstrap a fresh secrets store. Non-mapping YAML payloads raise.
        """
        if not self._secrets_path.exists():
            return {}
        ciphertext = self._secrets_path.read_bytes()
        if not ciphertext:
            return {}
        plaintext = self._backend.decrypt(ciphertext)
        raw = self._parse_yaml(plaintext)
        if raw is None:
            return {}
        if not isinstance(raw, dict):
            raise ValueError(
                "secrets.age payload did not parse to a YAML mapping; "
                f"got {type(raw).__name__}"
            )
        # Copy to keep caller mutations from touching cached objects.
        return dict(raw)

    def _write_mapping_atomic(self, mapping: dict[str, Any]) -> None:
        plaintext = self._dump_yaml(mapping)
        ciphertext = self._backend.encrypt(plaintext)
        self._secrets_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._secrets_path.with_suffix(self._secrets_path.suffix + ".tmp")
        tmp.write_bytes(ciphertext)
        os.replace(tmp, self._secrets_path)

    @staticmethod
    def _parse_yaml(data: bytes) -> Any:
        import yaml  # lazy

        return yaml.safe_load(data.decode("utf-8"))

    @staticmethod
    def _dump_yaml(mapping: dict[str, Any]) -> bytes:
        import yaml  # lazy

        return yaml.safe_dump(mapping, sort_keys=True).encode("utf-8")


# ----------------------------------------------------------------------
# Singleton factory
# ----------------------------------------------------------------------


_DEFAULT_SECRETS_PATH_ENV = "KOSMOS_SECRETS_PATH"
_DEFAULT_IDENTITY_PATH_ENV = "KOSMOS_AGE_IDENTITY_PATH"
_DEFAULT_SECRETS_PATH = Path("~/.kosmos/secrets/secrets.age")

_singleton: AgeFileSecretsAdapter | None = None


def get_age_file_secrets_adapter(
    *,
    secrets_path: Path | None = None,
    backend: AgeBackend | None = None,
) -> AgeFileSecretsAdapter:
    """Return the module-level singleton, constructing on first call.

    Parameters are honored only on first call; subsequent calls return
    the cached instance regardless of arguments. Tests should build
    instances directly rather than relying on the singleton.
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    if secrets_path is None:
        env_path = os.environ.get(_DEFAULT_SECRETS_PATH_ENV)
        secrets_path = Path(env_path).expanduser() if env_path else _DEFAULT_SECRETS_PATH.expanduser()

    if backend is None:
        env_identity = os.environ.get(_DEFAULT_IDENTITY_PATH_ENV)
        if not env_identity:
            raise EnvironmentError(
                f"{_DEFAULT_IDENTITY_PATH_ENV} must be set to construct the "
                "default PyrageBackend; either set it or pass backend= explicitly."
            )
        backend = PyrageBackend(Path(env_identity).expanduser())

    _singleton = AgeFileSecretsAdapter(secrets_path=secrets_path, backend=backend)
    return _singleton
