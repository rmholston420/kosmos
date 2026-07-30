"""Praxis constitution boot-verification subsystem (Stage 2.1, ADR-032).

Public surface — the only names other modules should import:

- :class:`ConstitutionLoader` — boot-time load-and-verify orchestrator
- :class:`ConstitutionArtifact` — verified immutable payload
- :class:`ConstitutionVerifier` — Ed25519 signature verifier
- :class:`ConstitutionError` (and subclasses) — failure hierarchy
"""

from __future__ import annotations

from plugins.praxis.constitution.errors import (
    ConstitutionError,
    ConstitutionMalformedError,
    ConstitutionNotFoundError,
    ConstitutionTamperError,
)
from plugins.praxis.constitution.loader import (
    ConstitutionArtifact,
    ConstitutionLoader,
)
from plugins.praxis.constitution.verifier import ConstitutionVerifier

__all__ = [
    "ConstitutionArtifact",
    "ConstitutionError",
    "ConstitutionLoader",
    "ConstitutionMalformedError",
    "ConstitutionNotFoundError",
    "ConstitutionTamperError",
    "ConstitutionVerifier",
]
