"""Loop Guard — detects repetitive agent action cycles.

Vendored from Forge-OH ``bff/services/loop_guard.py`` at commit
``9e7209d`` (MIT). Repurposed inside the Tektos executor to catch
fingerprint-level repeats across ``TektosExecutorLoop.run_plan``
attempts — e.g. two successive patch attempts producing the same
``git apply --check`` rejection on the same target with the same
approach classification.

Per ADR-080 the retry budget is ``TEKTOS_EXECUTOR_MAX_ATTEMPTS = 2``
(one initial + one self-correction), so the LoopGuard's default
``threshold=3`` will not trigger within a single plan. Its usefulness
is **across** plans issued against the same worktree — when a plan
is re-executed after a failure, the guard's ``history`` (if the
instance is reused) or a persistent variant can still surface a
degenerate loop. The initial wiring in Stage 3.14b holds a
per-executor-request instance, which means it is effectively a
no-op for the current retry budget; keeping the vendored code
intact preserves the escalation semantics for later stages (3.15+)
where retries widen and streaming feedback lands.

Provenance
----------
- **Source:** https://github.com/rmholston420/Forge-OH/blob/9e7209d/bff/services/loop_guard.py
- **Commit / Version:** 9e7209d (2026-08-01)
- **License:** MIT (© 2026 rmholston420)
- **Modifications:** module-level docstring + type-hint refresh
  (``deque[str]`` instead of ``Deque[str]``) + inline comment
  polish; behavior unchanged.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

__all__ = ["ActionFingerprint", "LoopGuard"]


@dataclass(frozen=True, slots=True)
class ActionFingerprint:
    """A three-tuple identifying an agent action.

    Attributes
    ----------
    operation_class:
        Coarse action bucket. Tektos will populate with values such
        as ``"edit_file"``, ``"run_test"``, ``"rewrite_func"``.
    target:
        Normalized file path or function name being acted on.
    approach:
        Broad classification of the approach taken — ``"syntax"``,
        ``"logic"``, ``"structural"``. The ``suggest_escalation``
        map keys off this string.
    """

    operation_class: str
    target: str
    approach: str


class LoopGuard:
    """Bounded-window repeated-fingerprint detector.

    Parameters
    ----------
    window:
        Number of recent fingerprints to retain. Older entries are
        evicted FIFO.
    threshold:
        Minimum count within the window that constitutes a loop.

    Notes
    -----
    ``is_looping`` appends the current fingerprint **before** counting,
    so a call with the ``threshold``-th occurrence of the same key
    returns ``True`` — not the ``threshold+1``-th. This matches
    Forge-OH's original semantics; a fingerprint deque of length
    ``window`` can therefore never dilute a genuine loop.
    """

    def __init__(self, window: int = 5, threshold: int = 3) -> None:
        self.history: deque[str] = deque(maxlen=window)
        self.threshold = threshold

    def fingerprint(self, fp: ActionFingerprint) -> str:
        """Return the deterministic colon-joined key for ``fp``.

        Hashing would add collision risk with no benefit — the key
        space is small and deterministic.
        """
        return f"{fp.operation_class}:{fp.target}:{fp.approach}"

    def is_looping(self, fp: ActionFingerprint) -> bool:
        """Append ``fp`` to history and report whether it now loops."""
        h = self.fingerprint(fp)
        self.history.append(h)  # append first
        count = sum(1 for x in self.history if x == h)  # then count
        return count >= self.threshold

    def suggest_escalation(self, fp: ActionFingerprint) -> str:
        """Suggest a broader-scope approach after a loop is detected.

        Falls back to ``"delegate_to_human"`` when ``fp.approach`` is
        not one of the mapped stages. Tektos will consume this string
        in Stage 3.15+ when the retry budget widens; Stage 3.14b holds
        it verbatim from the upstream to avoid divergence.
        """
        escalation_map = {
            "syntax": "structural",
            "structural": "rewrite",
            "rewrite": "delegate_to_human",
        }
        return escalation_map.get(fp.approach, "delegate_to_human")

    def reset(self) -> None:
        """Discard all recorded fingerprints."""
        self.history.clear()
