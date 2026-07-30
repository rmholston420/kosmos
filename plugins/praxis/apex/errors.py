"""APEX Change Approval error hierarchy (ADR-033).

Single ``ApexError`` base so callers can catch one exception type at the
approval boundary. Mirrors ``ConstitutionError`` hierarchy from Stage 2.1
(ADR-032).
"""

from __future__ import annotations

__all__ = [
    "ApexError",
    "ApprovalNotFoundError",
    "InvalidTransitionError",
    "TokenExpiredError",
    "TokenMalformedError",
    "TokenTamperError",
]


class ApexError(Exception):
    """Base for every APEX Change Approval error."""


class ApprovalNotFoundError(ApexError):
    """Raised when an ``approval_id`` cannot be resolved by Storage."""


class InvalidTransitionError(ApexError):
    """Raised when resolve() is called on a non-PENDING record.

    HUMAN_REVIEW and AUTONOMOUS records may auto-approve immediately;
    HUMAN_REQUIRED records stay PENDING until resolve() lands. A second
    resolve() on the same approval_id is a caller bug.
    """


class TokenMalformedError(ApexError):
    """Raised when the mobile approval token fails to parse.

    Distinct from ``TokenTamperError`` because malformed tokens never
    reached the signature-verify step — they were rejected at decode.
    """


class TokenExpiredError(ApexError):
    """Raised when a mobile approval token's ``exp`` is in the past.

    Tokens have a 24h TTL per spec §17.13.
    """


class TokenTamperError(ApexError):
    """Raised when the mobile approval token's signature fails to verify.

    The token payload MAY be parseable and MAY have a future ``exp``, but
    the Ed25519 signature does not match the pubkey. Treat as a security
    event and log accordingly (out of scope for this module).
    """
