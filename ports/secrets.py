"""SecretsPort — formal port for credential/key retrieval (ADR-024).

Per ADR-024, Kosmos ships an age-encrypted file backend as the primary
SecretsPort adapter for Stage 1.5+. `lease()` (spec §4.1) is deferred to a
future ADR triggered by Tektos per-task secret scoping in Stage 2.

Do not read secrets via `os.environ` in domain code. Route all credential
retrieval through this port.

Domain code should hold ``SecretValue`` instances and call ``.reveal()`` at
the last possible moment before handing the raw string to an adapter. Every
call to ``.reveal()`` is a review point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

__all__ = ["SecretValue", "SecretsPort"]


@dataclass(frozen=True, slots=True)
class SecretValue:
    """A redacting wrapper around a raw secret string.

    - ``repr(sv)`` and ``str(sv)`` return ``"SecretValue(***)"``.
    - ``sv == sv2`` compares redacted repr, so two different secret values
      never appear equal in log output. Use ``.reveal() == other.reveal()``
      for real equality when needed (rare — usually you want ``rotate()``).
    - Pickling is refused so accidental serialization to disk / queue /
      cache does not leak the raw value.
    - ``hash(sv)`` operates on the redacted repr, keeping dicts/sets safe
      to log without exposing keys.

    The raw value is only reachable through ``.reveal()``. Grep for that
    verb to audit every plaintext access:

        grep -rn '\\.reveal()' kosmos/
    """

    _value: str = field(repr=False)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "SecretValue(***)"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return "SecretValue(***)"

    def __eq__(self, other: object) -> bool:
        # Redacted-repr equality: identical instances remain equal, distinct
        # secrets never compare equal in logs/diagnostics.
        return isinstance(other, SecretValue) and repr(self) == repr(other)

    def __hash__(self) -> int:
        return hash(repr(self))

    def __reduce__(self) -> Any:
        raise TypeError(
            "SecretValue refuses pickling to prevent accidental persistence "
            "of raw secret material. Store the encrypted source (secrets.age) "
            "and re-derive at read time via SecretsPort.get_secret()."
        )

    def __reduce_ex__(self, protocol: int) -> Any:  # noqa: D401 - matches stdlib
        return self.__reduce__()

    def reveal(self) -> str:
        """Return the raw secret string. Every call is a review point."""
        return self._value


@runtime_checkable
class SecretsPort(Protocol):
    """Formal port for secret retrieval + rotation.

    ADR-024 fixes the surface at:
      get_secret / put_secret / rotate / is_healthy / close

    The ``lease()`` method from spec §4.1 is deferred — a later ADR will
    add it when Tektos per-task scoping (spec §18.6) is implemented.

    Contract invariants (enforced by contract tests):
      1. ``get_secret(unknown_key)`` raises ``KeyError``.
      2. ``get_secret(k)`` returns a ``SecretValue``, never a raw ``str``.
      3. ``put_secret`` is create-or-update; no silent duplicate errors.
      4. ``rotate(k, v)`` is equivalent in effect to ``put_secret(k, v)``
         for existing keys and raises ``KeyError`` for unknown keys — the
         distinction preserves an audit signal (rotate = intentional
         key-material replacement; put = first-time set).
      5. ``is_healthy()`` never raises; returns ``False`` on any error.
      6. ``close()`` is idempotent.
    """

    async def get_secret(self, key: str) -> SecretValue: ...

    async def put_secret(self, key: str, value: str) -> None: ...

    async def rotate(self, key: str, new_value: str) -> None: ...

    async def is_healthy(self) -> bool: ...

    async def close(self) -> None: ...
