"""ADR-010 eval ResourcePort policy.

Per ADR-029 (ResourcePort priority queue), all GPU-bound work in Kosmos
must declare a priority tier so the scheduler can arbitrate. The ADR-010
eval runs at BACKGROUND priority — never preempt user-facing work on
Colossus. Foreground plugin work (research, meditation feedback, agent
inference) always takes precedence.

Metrics collection (nvidia-smi sampling) also runs through the policy so
peaks are recorded even when the harness itself is paused by the scheduler.
"""

from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass


@dataclass(slots=True)
class GPUSample:
    utilization_pct: float
    memory_used_gb: float
    temperature_c: float = 0.0


def sample_gpu(device_id: int = 0) -> GPUSample:
    """Snapshot nvidia-smi utilization + VRAM + temperature for one GPU.

    Returns zeros if nvidia-smi is unavailable (sandbox path).
    """
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                f"--id={device_id}",
                "--query-gpu=utilization.gpu,memory.used,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5.0,
        )
        parts = [p.strip() for p in out.strip().split(",")]
        util_str, mem_mib_str = parts[0], parts[1]
        temp_str = parts[2] if len(parts) > 2 else "0"
        return GPUSample(
            utilization_pct=float(util_str),
            memory_used_gb=float(mem_mib_str) / 1024.0,
            temperature_c=float(temp_str),
        )
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        return GPUSample(0.0, 0.0, 0.0)


def wait_for_cooldown(
    target_c: float = 70.0,
    min_seconds: float = 30.0,
    max_seconds: float = 300.0,
    poll_seconds: float = 5.0,
    device_id: int = 0,
    logger=None,
) -> tuple[float, float]:
    """Sleep until GPU temperature drops to ``target_c`` or ``max_seconds`` elapses.

    Always sleeps at least ``min_seconds`` for post-load thermal soak — nvidia-smi
    temp reads chase actual junction temp with a ~10-30s lag, so we don't trust an
    immediately-cool reading right after a workload ends.

    Returns ``(waited_seconds, final_temperature_c)``. Safe on hosts without
    nvidia-smi: ``sample_gpu`` returns 0.0 and the function returns after
    ``min_seconds`` without polling.
    """
    start = time.monotonic()
    time.sleep(min_seconds)
    while True:
        elapsed = time.monotonic() - start
        if elapsed >= max_seconds:
            sample = sample_gpu(device_id)
            if logger is not None:
                logger.warning(
                    "cooldown timeout: waited %.1fs, temp=%.1fC (target %.1fC)",
                    elapsed,
                    sample.temperature_c,
                    target_c,
                )
            return (elapsed, sample.temperature_c)
        sample = sample_gpu(device_id)
        if sample.temperature_c > 0.0 and sample.temperature_c <= target_c:
            if logger is not None:
                logger.info(
                    "cooldown done: waited %.1fs, temp=%.1fC (target %.1fC)",
                    elapsed,
                    sample.temperature_c,
                    target_c,
                )
            return (elapsed, sample.temperature_c)
        if sample.temperature_c == 0.0:
            # nvidia-smi not readable — fall through after min_seconds only.
            return (elapsed, 0.0)
        time.sleep(poll_seconds)


class GPUMonitor:
    """Background thread sampling nvidia-smi at 1 Hz, tracking peak metrics.

    In addition to observation-only peak tracking, the monitor supports an
    optional in-trial thermal-abort threshold. Callers pass
    ``thermal_abort_at_c`` at construction; if any sample meets or exceeds
    that temperature, ``thermal_exceeded()`` returns True and
    ``abort_reason`` captures the breach for the artifact.

    This gives the harness (see ``harness/odr._invoke_once``) an actionable
    signal to cancel a running ``ainvoke`` task before the RTX 5090 climbs
    into driver-crash territory (~88 C on Colossus, empirically).
    """

    def __init__(
        self,
        device_id: int = 0,
        sample_hz: float = 1.0,
        thermal_abort_at_c: float | None = None,
    ) -> None:
        self.device_id = device_id
        self._interval = 1.0 / sample_hz
        self._peak_util = 0.0
        self._peak_vram = 0.0
        self._peak_temp = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # Thermal-abort surface. When ``thermal_abort_at_c`` is set and any
        # sample meets/exceeds it, ``_thermal_event`` is set and
        # ``_abort_reason`` records the breach.
        self._thermal_abort_at_c = thermal_abort_at_c
        self._thermal_event = threading.Event()
        self._abort_reason: str | None = None
        self._abort_temp: float | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _loop(self) -> None:
        while not self._stop.is_set():
            sample = sample_gpu(self.device_id)
            if sample.utilization_pct > self._peak_util:
                self._peak_util = sample.utilization_pct
            if sample.memory_used_gb > self._peak_vram:
                self._peak_vram = sample.memory_used_gb
            if sample.temperature_c > self._peak_temp:
                self._peak_temp = sample.temperature_c
            # Thermal-abort check: if a threshold is configured and this
            # sample meets/exceeds it, latch the event exactly once.
            if (
                self._thermal_abort_at_c is not None
                and sample.temperature_c > 0.0
                and sample.temperature_c >= self._thermal_abort_at_c
                and not self._thermal_event.is_set()
            ):
                self._abort_temp = sample.temperature_c
                self._abort_reason = (
                    f"thermal_abort: sample {sample.temperature_c:.1f} C "
                    f">= threshold {self._thermal_abort_at_c:.1f} C"
                )
                self._thermal_event.set()
            time.sleep(self._interval)

    def thermal_exceeded(self) -> bool:
        return self._thermal_event.is_set()

    @property
    def thermal_event(self) -> threading.Event:
        """Expose the raw event for cross-thread / asyncio polling."""
        return self._thermal_event

    @property
    def abort_reason(self) -> str | None:
        return self._abort_reason

    @property
    def abort_temperature_c(self) -> float | None:
        return self._abort_temp

    @property
    def peak_utilization_pct(self) -> float:
        return self._peak_util

    @property
    def peak_vram_gb(self) -> float:
        return self._peak_vram

    @property
    def peak_temperature_c(self) -> float:
        return self._peak_temp


__all__ = ["GPUMonitor", "GPUSample", "sample_gpu", "wait_for_cooldown"]
