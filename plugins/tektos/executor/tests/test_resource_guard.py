"""Colossus resource-envelope guard (ADR-080).

Covers:

* skip env var short-circuit + WARNING log
* both queries ok, both floors met -> OK
* VRAM below floor -> BLOCKED (reason names VRAM)
* RAM below floor -> BLOCKED (reason names RAM)
* VRAM checked before RAM (both unmet -> reason still names VRAM first)
* nvidia-smi missing on PATH -> UNAVAILABLE
* nvidia-smi timeout -> UNAVAILABLE
* nvidia-smi exit non-zero -> UNAVAILABLE
* nvidia-smi non-int row -> UNAVAILABLE
* multi-GPU output -> minimum-free wins
* /proc/meminfo missing -> UNAVAILABLE
* /proc/meminfo without MemAvailable -> UNAVAILABLE
* /proc/meminfo MemAvailable non-int -> UNAVAILABLE
* MemAvailable kB -> MiB conversion
* result.ok convenience property
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

from plugins.tektos.executor.policy import (
    TEKTOS_EXECUTOR_RAM_FLOOR_MIB,
    TEKTOS_EXECUTOR_VRAM_FLOOR_MIB,
)
from plugins.tektos.executor.resource_guard import (
    SKIP_ENV_VAR,
    ColossusResourceGuard,
    GuardVerdict,
)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def meminfo(tmp_path: Path) -> Path:
    """A /proc/meminfo-shaped file with MemAvailable = 16 GiB by default."""
    p = tmp_path / "meminfo"
    p.write_text(
        "MemTotal:      131072000 kB\n"
        "MemFree:         2000000 kB\n"
        "MemAvailable:   16777216 kB\n"  # exactly 16 GiB
        "Buffers:          100000 kB\n",
        encoding="utf-8",
    )
    return p


def _guard(
    *,
    monkeypatch: pytest.MonkeyPatch,
    stdout: str = "24000\n",
    returncode: int = 0,
    timeout: bool = False,
    oserror: bool = False,
    nvidia_smi_bin: str | None = "/usr/bin/nvidia-smi",
    meminfo: Path,
    env: dict[str, str] | None = None,
    vram_floor_mib: int = TEKTOS_EXECUTOR_VRAM_FLOOR_MIB,
    ram_floor_mib: int = TEKTOS_EXECUTOR_RAM_FLOOR_MIB,
) -> ColossusResourceGuard:
    """Build a guard with subprocess.run patched to a scripted response."""

    def fake_run(argv, **kwargs):  # noqa: ANN001, ANN003 — subprocess signature
        if timeout:
            raise subprocess.TimeoutExpired(argv, kwargs.get("timeout", 3.0))
        if oserror:
            raise OSError("nvidia-smi vanished")
        return subprocess.CompletedProcess(
            argv, returncode, stdout=stdout, stderr="stderr!"
        )

    monkeypatch.setattr(
        "plugins.tektos.executor.resource_guard.subprocess.run",
        fake_run,
    )
    return ColossusResourceGuard(
        vram_floor_mib=vram_floor_mib,
        ram_floor_mib=ram_floor_mib,
        nvidia_smi_bin=nvidia_smi_bin,
        meminfo_path=meminfo,
        env=env if env is not None else {},
    )


# ── Skip env ──────────────────────────────────────────────────────────


def test_skip_env_short_circuits_ok(
    monkeypatch: pytest.MonkeyPatch,
    meminfo: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    called = {"n": 0}

    def blow_up(*args, **kwargs):  # noqa: ANN002, ANN003
        called["n"] += 1
        raise AssertionError("skip path must not touch subprocess")

    monkeypatch.setattr(
        "plugins.tektos.executor.resource_guard.subprocess.run", blow_up
    )
    guard = ColossusResourceGuard(
        nvidia_smi_bin="/usr/bin/nvidia-smi",
        meminfo_path=meminfo,
        env={SKIP_ENV_VAR: "1"},
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.OK
    assert r.ok
    assert r.vram_free_mib is None
    assert r.ram_available_mib is None
    assert r.reason == ""
    assert called["n"] == 0
    # WARNING must be emitted so the audit trail records the bypass.
    assert any(
        SKIP_ENV_VAR in rec.getMessage() for rec in caplog.records
    ), caplog.text


def test_skip_env_wrong_value_does_not_short_circuit(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    # Only "1" activates the skip; anything else (0, empty, "true") is
    # ignored so the guard remains fail-closed by default.
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="24000\n",
        meminfo=meminfo,
        env={SKIP_ENV_VAR: "true"},
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.OK
    assert r.vram_free_mib == 24000  # actually queried


# ── Happy paths ───────────────────────────────────────────────────────


def test_both_ok(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch, stdout="24000\n", meminfo=meminfo
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.OK
    assert r.vram_free_mib == 24000
    assert r.ram_available_mib == 16777216 // 1024  # 16384 MiB
    assert r.reason == ""
    assert r.ok is True


def test_multi_gpu_uses_minimum(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="30000\n21000\n25000\n",
        meminfo=meminfo,
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.OK
    assert r.vram_free_mib == 21000


# ── Blocked paths ─────────────────────────────────────────────────────


def test_vram_below_floor_blocks(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch, stdout="15000\n", meminfo=meminfo
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.BLOCKED
    assert r.vram_free_mib == 15000
    assert r.ram_available_mib == 16384
    assert "VRAM 15000" in r.reason
    assert not r.ok


def test_ram_below_floor_blocks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    small_ram = tmp_path / "meminfo-small"
    small_ram.write_text("MemAvailable:  4194304 kB\n", encoding="utf-8")
    guard = _guard(
        monkeypatch=monkeypatch, stdout="24000\n", meminfo=small_ram
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.BLOCKED
    assert r.ram_available_mib == 4096  # 4 GiB
    assert "RAM 4096" in r.reason


def test_vram_checked_before_ram(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Both floors unmet — reason must name VRAM (checked first).
    small_ram = tmp_path / "meminfo-small"
    small_ram.write_text("MemAvailable:  4194304 kB\n", encoding="utf-8")
    guard = _guard(
        monkeypatch=monkeypatch, stdout="15000\n", meminfo=small_ram
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.BLOCKED
    # Reason names VRAM (checked first). It must NOT mention the RAM
    # value — note "VRAM" contains "RAM", so we assert on the
    # numeric value instead of the substring.
    assert "VRAM 15000" in r.reason
    assert "4096" not in r.reason


# ── UNAVAILABLE paths ─────────────────────────────────────────────────


def test_nvidia_smi_missing(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="24000\n",
        meminfo=meminfo,
        nvidia_smi_bin=None,  # binary not on PATH
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE
    assert r.vram_free_mib is None
    assert r.ram_available_mib == 16384  # ram query still ran
    assert "nvidia-smi" in r.reason


def test_nvidia_smi_timeout(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch, timeout=True, meminfo=meminfo
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE
    assert r.vram_free_mib is None


def test_nvidia_smi_oserror(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch, oserror=True, meminfo=meminfo
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE


def test_nvidia_smi_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="",
        returncode=9,
        meminfo=meminfo,
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE


def test_nvidia_smi_garbage_row(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="24000\nnot-an-int\n",
        meminfo=meminfo,
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE


def test_nvidia_smi_empty_output(
    monkeypatch: pytest.MonkeyPatch, meminfo: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch, stdout="\n\n", meminfo=meminfo
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE
    assert r.vram_free_mib is None


def test_meminfo_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="24000\n",
        meminfo=tmp_path / "does-not-exist",
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE
    assert r.ram_available_mib is None
    assert r.vram_free_mib == 24000  # vram query still ran
    assert "meminfo" in r.reason.lower()


def test_meminfo_no_memavailable_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    partial = tmp_path / "meminfo-partial"
    partial.write_text("MemTotal: 100 kB\nMemFree: 50 kB\n", encoding="utf-8")
    guard = _guard(
        monkeypatch=monkeypatch, stdout="24000\n", meminfo=partial
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE
    assert r.ram_available_mib is None


def test_meminfo_memavailable_non_int(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bad = tmp_path / "meminfo-bad"
    bad.write_text("MemAvailable: abc kB\n", encoding="utf-8")
    guard = _guard(
        monkeypatch=monkeypatch, stdout="24000\n", meminfo=bad
    )
    r = guard.check()
    assert r.verdict is GuardVerdict.UNAVAILABLE


# ── Unit conversion ───────────────────────────────────────────────────


def test_memavailable_kib_to_mib_floor_division(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # 9000 kB is 8.789 MiB; floor-divided that's 8 MiB. Verifies we
    # never round up (rounding up would let the guard pass on a real
    # sub-MiB reading).
    p = tmp_path / "meminfo-tiny"
    p.write_text("MemAvailable: 9000 kB\n", encoding="utf-8")
    guard = _guard(
        monkeypatch=monkeypatch,
        stdout="24000\n",
        meminfo=p,
        ram_floor_mib=1,  # trivial floor so RAM alone doesn't block
    )
    r = guard.check()
    assert r.ram_available_mib == 8
