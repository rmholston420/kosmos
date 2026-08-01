"""Colossus resource-envelope guard for the Tektos executor (ADR-080).

Refuses ``/api/tektos/plan/{id}/execute`` when either the free-VRAM
floor or the available-RAM floor is unmet. Runs at endpoint entry —
before any sandbox or LLM work — so a low-VRAM condition never
half-provisions an execution.

Design notes
------------
- ``nvidia-smi`` is invoked as a plain subprocess (``--query-gpu``
  csv output). The RTX 5090 (Blackwell SM_120) is the only GPU on
  Colossus; if ``nvidia-smi`` returns multiple rows we take the
  minimum free VRAM across them so the guard remains conservative.
- ``/proc/meminfo`` is read directly (kernel-provided text file, no
  subprocess). ``MemAvailable`` is the kernel's own estimate of how
  much RAM can be handed to a new process without swapping — a
  materially better signal than ``MemFree``.
- The guard is **fail-closed**: if either query cannot produce a
  number, the guard result is ``unavailable`` and the endpoint MUST
  refuse. An explicit escape hatch
  (``KOSMOS_EXECUTOR_SKIP_RESOURCE_GUARD=1``) is provided for
  developer laptops; systemd unit files do not set it.
- No new pip deps. No new port. ADR-007-compliant: this module only
  imports from stdlib and ``plugins.tektos.executor.policy``.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from plugins.tektos.executor.policy import (
    TEKTOS_EXECUTOR_RAM_FLOOR_MIB,
    TEKTOS_EXECUTOR_VRAM_FLOOR_MIB,
)

log = logging.getLogger(__name__)

__all__ = [
    "GuardResult",
    "GuardVerdict",
    "ColossusResourceGuard",
    "SKIP_ENV_VAR",
]

_AUTO_DETECT = object()
"""Sentinel default for :class:`ColossusResourceGuard`'s
``nvidia_smi_bin`` argument. Distinguishes "caller didn't pass
anything, discover via ``shutil.which``" from an explicit
``nvidia_smi_bin=None`` meaning "binary is known to be missing"."""


# ── Constants ─────────────────────────────────────────────────────────

SKIP_ENV_VAR = "KOSMOS_EXECUTOR_SKIP_RESOURCE_GUARD"
"""Escape hatch. When set to ``"1"``, :meth:`ColossusResourceGuard.check`
returns an ``ok`` verdict without touching ``nvidia-smi`` or
``/proc/meminfo``. Systemd unit files MUST NOT set this — verified by
the endpoint tests in step 2b."""

_NVIDIA_SMI_ARGS: tuple[str, ...] = (
    "--query-gpu=memory.free",
    "--format=csv,noheader,nounits",
)
"""Args to ``nvidia-smi``. csv/noheader/nounits gives us pure integer
rows (MiB free per GPU), one row per device."""

_NVIDIA_SMI_TIMEOUT_SEC = 3.0
"""Hard cap on ``nvidia-smi``. If the driver is wedged, we treat it
the same as ``nvidia-smi`` missing (fail-closed)."""

_MEMINFO_PATH = Path("/proc/meminfo")
"""Kernel-provided text file. Never redefined in real code — the
``meminfo_path`` argument on :class:`ColossusResourceGuard` exists
only so tests can point at a fixture without monkeypatching the
module-level constant."""


# ── Verdicts ──────────────────────────────────────────────────────────


class GuardVerdict(str, Enum):
    """Three-way verdict returned by :meth:`ColossusResourceGuard.check`.

    ``ok``
        Both floors met. Executor may proceed.
    ``blocked``
        A floor was unmet. Executor MUST refuse (HTTP 503) and log
        the observed values.
    ``unavailable``
        A query could not produce a number (``nvidia-smi`` missing,
        driver wedged, ``/proc/meminfo`` unreadable). Fail-closed:
        executor MUST refuse.
    """

    OK = "ok"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class GuardResult:
    """Result of one :meth:`ColossusResourceGuard.check` call.

    Attributes
    ----------
    verdict:
        Overall verdict; see :class:`GuardVerdict`.
    vram_free_mib:
        Observed free VRAM in MiB (minimum across GPUs). ``None`` when
        ``nvidia-smi`` was missing, wedged, or returned nothing
        parseable.
    ram_available_mib:
        Observed ``MemAvailable`` in MiB. ``None`` when
        ``/proc/meminfo`` could not be read or parsed.
    reason:
        Human-readable one-line reason. Empty string when
        ``verdict == OK``.
    """

    verdict: GuardVerdict
    vram_free_mib: int | None
    ram_available_mib: int | None
    reason: str

    @property
    def ok(self) -> bool:
        """True iff the executor is cleared to proceed."""
        return self.verdict is GuardVerdict.OK


# ── Guard ─────────────────────────────────────────────────────────────


class ColossusResourceGuard:
    """Query the local host's free VRAM + available RAM.

    Parameters
    ----------
    vram_floor_mib:
        Minimum free VRAM to pass. Defaults to the ADR-080-locked
        :data:`~plugins.tektos.executor.policy.TEKTOS_EXECUTOR_VRAM_FLOOR_MIB`.
    ram_floor_mib:
        Minimum available RAM to pass. Defaults to the ADR-080-locked
        :data:`~plugins.tektos.executor.policy.TEKTOS_EXECUTOR_RAM_FLOOR_MIB`.
    nvidia_smi_bin:
        Path to ``nvidia-smi``. Defaults to
        ``shutil.which("nvidia-smi")``; ``None`` in the resolved value
        means the binary is missing.
    meminfo_path:
        Path to ``/proc/meminfo``. Test fixtures override this to
        point at a tmp file — production callers never pass this.
    env:
        Environment-variable lookup. Defaults to ``os.environ``. Tests
        may pass a plain dict.
    """

    def __init__(
        self,
        *,
        vram_floor_mib: int = TEKTOS_EXECUTOR_VRAM_FLOOR_MIB,
        ram_floor_mib: int = TEKTOS_EXECUTOR_RAM_FLOOR_MIB,
        nvidia_smi_bin: str | None = _AUTO_DETECT,  # type: ignore[assignment]
        meminfo_path: Path = _MEMINFO_PATH,
        env: dict[str, str] | os._Environ[str] | None = None,
    ) -> None:
        self._vram_floor = vram_floor_mib
        self._ram_floor = ram_floor_mib
        # Sentinel: only auto-detect when the caller passed nothing.
        # Explicit ``None`` means "binary is missing" and must be
        # honored so tests can force the UNAVAILABLE branch even on a
        # host where ``nvidia-smi`` is on PATH.
        if nvidia_smi_bin is _AUTO_DETECT:
            self._nvidia_smi_bin = shutil.which("nvidia-smi")
        else:
            self._nvidia_smi_bin = nvidia_smi_bin
        self._meminfo_path = meminfo_path
        self._env = env if env is not None else os.environ

    # ---- public API --------------------------------------------------

    def check(self) -> GuardResult:
        """Run both queries and return a :class:`GuardResult`.

        Semantics:

        * If ``KOSMOS_EXECUTOR_SKIP_RESOURCE_GUARD=1`` in ``env``,
          return ``OK`` immediately and log a WARNING. Both
          ``vram_free_mib`` and ``ram_available_mib`` are ``None`` on
          the skip path (nothing was measured).
        * Otherwise, query VRAM first, then RAM. If either query
          fails to produce a number, verdict is ``UNAVAILABLE``.
        * If both queries produce numbers and both meet their floors,
          verdict is ``OK``.
        * If both queries produce numbers but a floor is unmet, verdict
          is ``BLOCKED``. Reason names the first unmet floor
          (VRAM checked before RAM).
        """
        if self._env.get(SKIP_ENV_VAR) == "1":
            log.warning(
                "ColossusResourceGuard skipped via %s=1 (dev-only escape hatch)",
                SKIP_ENV_VAR,
            )
            return GuardResult(
                verdict=GuardVerdict.OK,
                vram_free_mib=None,
                ram_available_mib=None,
                reason="",
            )

        vram = self._query_vram_free_mib()
        ram = self._query_ram_available_mib()

        if vram is None or ram is None:
            missing: list[str] = []
            if vram is None:
                missing.append("nvidia-smi VRAM query")
            if ram is None:
                missing.append("/proc/meminfo RAM query")
            return GuardResult(
                verdict=GuardVerdict.UNAVAILABLE,
                vram_free_mib=vram,
                ram_available_mib=ram,
                reason=f"resource query unavailable: {', '.join(missing)}",
            )

        if vram < self._vram_floor:
            return GuardResult(
                verdict=GuardVerdict.BLOCKED,
                vram_free_mib=vram,
                ram_available_mib=ram,
                reason=(
                    f"free VRAM {vram} MiB < floor {self._vram_floor} MiB"
                ),
            )

        if ram < self._ram_floor:
            return GuardResult(
                verdict=GuardVerdict.BLOCKED,
                vram_free_mib=vram,
                ram_available_mib=ram,
                reason=(
                    f"available RAM {ram} MiB < floor {self._ram_floor} MiB"
                ),
            )

        return GuardResult(
            verdict=GuardVerdict.OK,
            vram_free_mib=vram,
            ram_available_mib=ram,
            reason="",
        )

    # ---- private queries --------------------------------------------

    def _query_vram_free_mib(self) -> int | None:
        """Return the minimum free VRAM across all GPUs, or None.

        None means ``nvidia-smi`` is missing, the subprocess timed out,
        the subprocess exited non-zero, or no row parsed as an integer.
        """
        if not self._nvidia_smi_bin:
            log.debug("nvidia-smi not found on PATH")
            return None

        try:
            proc = subprocess.run(
                [self._nvidia_smi_bin, *_NVIDIA_SMI_ARGS],
                capture_output=True,
                text=True,
                timeout=_NVIDIA_SMI_TIMEOUT_SEC,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            log.warning("nvidia-smi failed: %s", exc)
            return None

        if proc.returncode != 0:
            log.warning(
                "nvidia-smi exit %d: %s",
                proc.returncode,
                proc.stderr.strip(),
            )
            return None

        values: list[int] = []
        for raw_line in proc.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                values.append(int(line))
            except ValueError:
                log.warning("nvidia-smi row not an int: %r", line)
                # Any unparseable row means we can't trust the reading.
                return None

        if not values:
            return None
        return min(values)

    def _query_ram_available_mib(self) -> int | None:
        """Return ``MemAvailable`` from ``/proc/meminfo`` in MiB, or None.

        ``/proc/meminfo`` reports ``MemAvailable`` in KiB. We convert to
        MiB via integer division (``// 1024``) so the value compares
        cleanly against the MiB-denominated floor.
        """
        try:
            text = self._meminfo_path.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("meminfo unreadable: %s", exc)
            return None

        for raw_line in text.splitlines():
            if not raw_line.startswith("MemAvailable:"):
                continue
            parts = raw_line.split()
            # Expected shape: ["MemAvailable:", "123456", "kB"]
            if len(parts) < 2:
                return None
            try:
                kib = int(parts[1])
            except ValueError:
                return None
            return kib // 1024
        return None
