"""Constitution loader error hierarchy.

Stage 2.1 DoD: tampered constitution → boot refused.

The "boot refused" signal is a raised exception from
:meth:`ConstitutionLoader.__init__` or :meth:`ConstitutionLoader.verify`.
Every failure mode is a subclass of :class:`ConstitutionError` so callers
(kernel bootstrap, Praxis plugin init) can catch a single base class and
halt startup uniformly.
"""

from __future__ import annotations


class ConstitutionError(Exception):
    """Base class for all constitution loader failures."""


class ConstitutionNotFoundError(ConstitutionError):
    """A required artifact (yaml/json/sig/pubkey) is missing on disk."""


class ConstitutionMalformedError(ConstitutionError):
    """An artifact is present but cannot be parsed (bad YAML, bad JSON, bad base64)."""


class ConstitutionTamperError(ConstitutionError):
    """The constitution failed cryptographic verification.

    Raised when:
    - The Ed25519 signature does not verify against the pubkey and canonical JSON.
    - The on-disk JSON copy does not match the JCS canonicalization of the YAML
      payload (indicating either the YAML or the JSON has been altered
      out-of-band).
    """
