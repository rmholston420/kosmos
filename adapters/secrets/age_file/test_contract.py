"""Contract tests for AgeFileSecretsAdapter (Stage 1.5, ADR-024).

Uses ``InMemoryAgeBackend`` so tests do not require ``pyrage``. Real
crypto is exercised only in a Colossus smoke test outside this suite.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from adapters.secrets.age_file import (
    AgeBackend,
    AgeFileSecretsAdapter,
    InMemoryAgeBackend,
    PyrageBackend,
    get_age_file_secrets_adapter,
)
from ports.secrets import SecretValue, SecretsPort


# ---------------------------------------------------------------------------
# SecretValue invariants
# ---------------------------------------------------------------------------


def test_secret_value_repr_redacts() -> None:
    sv = SecretValue("hunter2")
    assert repr(sv) == "SecretValue(***)"
    assert str(sv) == "SecretValue(***)"
    assert "hunter2" not in repr(sv)


def test_secret_value_reveal_returns_raw() -> None:
    sv = SecretValue("hunter2")
    assert sv.reveal() == "hunter2"


def test_secret_value_equality_is_redacted_not_raw() -> None:
    # Two DIFFERENT secrets compare equal under redacted-repr equality —
    # this is intentional so accidental log-line comparisons never leak
    # a bit of raw-value information. Real equality goes through .reveal().
    a = SecretValue("hunter2")
    b = SecretValue("correcthorsebatterystaple")
    assert a == b
    assert a.reveal() != b.reveal()


def test_secret_value_hashable() -> None:
    sv = SecretValue("hunter2")
    d = {sv: 1}
    assert d[sv] == 1


def test_secret_value_refuses_pickle() -> None:
    sv = SecretValue("hunter2")
    with pytest.raises(TypeError, match="refuses pickling"):
        pickle.dumps(sv)


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def _make_adapter(tmp_path: Path) -> AgeFileSecretsAdapter:
    return AgeFileSecretsAdapter(
        secrets_path=tmp_path / "secrets.age",
        backend=InMemoryAgeBackend(),
    )


def test_age_file_adapter_satisfies_secrets_port_protocol(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    assert isinstance(adapter, SecretsPort)


def test_in_memory_backend_satisfies_age_backend_protocol() -> None:
    assert isinstance(InMemoryAgeBackend(), AgeBackend)


def test_pyrage_backend_type_satisfies_age_backend_protocol_shape() -> None:
    # We do not instantiate PyrageBackend (would try to read a real
    # identity file). We only assert the class has the two required
    # methods so shape conformance is guaranteed statically.
    assert callable(getattr(PyrageBackend, "decrypt", None))
    assert callable(getattr(PyrageBackend, "encrypt", None))


# ---------------------------------------------------------------------------
# get / put / rotate round-trip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_unknown_key_raises_key_error(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    with pytest.raises(KeyError):
        await adapter.get_secret("no-such-key")


@pytest.mark.asyncio
async def test_put_then_get_round_trip(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("GITHUB_TOKEN", "ghp_abc123")
    sv = await adapter.get_secret("GITHUB_TOKEN")
    assert isinstance(sv, SecretValue)
    assert sv.reveal() == "ghp_abc123"


@pytest.mark.asyncio
async def test_get_returns_secret_value_never_raw_str(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("K", "v")
    result = await adapter.get_secret("K")
    assert isinstance(result, SecretValue)
    assert not isinstance(result, str)


@pytest.mark.asyncio
async def test_put_secret_overwrites_existing(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("K", "v1")
    await adapter.put_secret("K", "v2")
    sv = await adapter.get_secret("K")
    assert sv.reveal() == "v2"


@pytest.mark.asyncio
async def test_put_secret_rejects_non_string_value(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    with pytest.raises(TypeError):
        await adapter.put_secret("K", 12345)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_rotate_replaces_existing_value(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("K", "old")
    await adapter.rotate("K", "new")
    sv = await adapter.get_secret("K")
    assert sv.reveal() == "new"


@pytest.mark.asyncio
async def test_rotate_unknown_key_raises_key_error(tmp_path: Path) -> None:
    # Rotate is intentionally distinct from put: it refuses unknown keys
    # so a rotate call cannot silently create a fresh secret and hide an
    # audit signal.
    adapter = _make_adapter(tmp_path)
    with pytest.raises(KeyError):
        await adapter.rotate("missing", "new")


@pytest.mark.asyncio
async def test_rotate_rejects_non_string_value(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("K", "v")
    with pytest.raises(TypeError):
        await adapter.rotate("K", 999)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Atomic file write
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_secrets_file_written_encrypted_not_plaintext(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("API_KEY", "sk-abc-super-secret")
    ciphertext = (tmp_path / "secrets.age").read_bytes()
    # Sentinel prefix from InMemoryAgeBackend proves encryption step ran.
    assert ciphertext.startswith(b"AGE-FAKE:")
    # And the plaintext bytes are the YAML the adapter wrote, wrapped —
    # so the raw value should appear only *inside* the ciphertext byte
    # region, past the sentinel. A production PyrageBackend would leave
    # no such trace.
    assert b"sk-abc-super-secret" in ciphertext[len(b"AGE-FAKE:") :]


@pytest.mark.asyncio
async def test_secrets_file_atomically_replaced(tmp_path: Path) -> None:
    """After a write, the .tmp sibling must not remain on disk."""
    adapter = _make_adapter(tmp_path)
    await adapter.put_secret("K", "v")
    files = sorted(p.name for p in tmp_path.iterdir())
    assert "secrets.age" in files
    assert not any(name.endswith(".tmp") for name in files)


@pytest.mark.asyncio
async def test_missing_secrets_file_treated_as_empty(tmp_path: Path) -> None:
    adapter = AgeFileSecretsAdapter(
        secrets_path=tmp_path / "does-not-exist.age",
        backend=InMemoryAgeBackend(),
    )
    with pytest.raises(KeyError):
        await adapter.get_secret("anything")
    # put_secret on a missing file bootstraps it
    await adapter.put_secret("bootstrap", "v")
    sv = await adapter.get_secret("bootstrap")
    assert sv.reveal() == "v"


# ---------------------------------------------------------------------------
# is_healthy / close
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_healthy_true_on_reachable_backend(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    assert await adapter.is_healthy() is True


@pytest.mark.asyncio
async def test_is_healthy_non_throwing_on_decrypt_failure(tmp_path: Path) -> None:
    # Write a file with a bad ciphertext prefix so decrypt would raise;
    # is_healthy must return False without propagating.
    bad_path = tmp_path / "secrets.age"
    bad_path.write_bytes(b"not-a-real-ciphertext")
    adapter = AgeFileSecretsAdapter(
        secrets_path=bad_path,
        backend=InMemoryAgeBackend(),
    )
    result = await adapter.is_healthy()
    assert result is False


@pytest.mark.asyncio
async def test_close_is_idempotent(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    await adapter.close()
    await adapter.close()  # second call must not raise


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_singleton_returns_same_instance(tmp_path: Path, monkeypatch) -> None:
    # Reset the module-level singleton before this test.
    import adapters.secrets.age_file.adapter as adapter_mod
    monkeypatch.setattr(adapter_mod, "_singleton", None)

    a = get_age_file_secrets_adapter(
        secrets_path=tmp_path / "s.age",
        backend=InMemoryAgeBackend(),
    )
    b = get_age_file_secrets_adapter(
        secrets_path=tmp_path / "other.age",
        backend=InMemoryAgeBackend(),
    )
    assert a is b
