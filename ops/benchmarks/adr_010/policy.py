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


def sample_gpu(device_id: int = 0) -> GPUSample:
    """Snapshot nvidia-smi utilization + VRAM for one GPU.

    Returns zeros if nvidia-smi is unavailable (sandbox path).
    """
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                f"--id={device_id}",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5.0,
        )
        util_str, mem_mib_str = out.strip().split(", ")
        return GPUSample(
            utilization_pct=float(util_str),
            memory_used_gb=float(mem_mib_str) / 1024.0,
        )
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        return GPUSample(0.0, 0.0)


class GPUMonitor:
    """Background thread sampling nvidia-smi at 1 Hz, tracking peak metrics."""

    def __init__(self, device_id: int = 0, sample_hz: float = 1.0) -> None:
        self.device_id = device_id
        self._interval = 1.0 / sample_hz
        self._peak_util = 0.0
        self._peak_vram = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

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
            time.sleep(self._interval)

    @property
    def peak_utilization_pct(self) -> float:
        return self._peak_util

    @property
    def peak_vram_gb(self) -> float:
        return self._peak_vram


__all__ = ["GPUMonitor", "GPUSample", "sample_gpu"]
