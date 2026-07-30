"""age-encrypted file backend for SecretsPort (ADR-024)."""

from adapters.secrets.age_file.adapter import (
    AgeFileSecretsAdapter,
    AgeBackend,
    PyrageBackend,
    InMemoryAgeBackend,
    get_age_file_secrets_adapter,
)

__all__ = [
    "AgeFileSecretsAdapter",
    "AgeBackend",
    "PyrageBackend",
    "InMemoryAgeBackend",
    "get_age_file_secrets_adapter",
]
