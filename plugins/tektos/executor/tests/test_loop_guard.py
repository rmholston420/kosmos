"""LoopGuard (vendored from Forge-OH 9e7209d, MIT).

Covers:

* fingerprint determinism + colon-join format
* is_looping fires on the threshold-th occurrence, not threshold+1
* distinct fingerprints do not accumulate together
* window bound: entries beyond ``window`` are evicted FIFO
* reset clears history
* suggest_escalation mapping + fallback to delegate_to_human
* ActionFingerprint is frozen (dataclass frozen=True)
* Custom window/threshold combinations behave as declared
"""

from __future__ import annotations

import pytest

from plugins.tektos.executor.loop_guard import ActionFingerprint, LoopGuard


def _fp(op: str = "edit_file", target: str = "a.py", approach: str = "syntax") -> ActionFingerprint:
    return ActionFingerprint(operation_class=op, target=target, approach=approach)


# ── ActionFingerprint ─────────────────────────────────────────────────


def test_action_fingerprint_is_frozen() -> None:
    fp = _fp()
    with pytest.raises(Exception):  # FrozenInstanceError
        fp.operation_class = "other"  # type: ignore[misc]


def test_fingerprint_key_is_colon_joined() -> None:
    guard = LoopGuard()
    assert guard.fingerprint(_fp("edit_file", "a.py", "syntax")) == "edit_file:a.py:syntax"


def test_fingerprint_key_is_deterministic() -> None:
    guard = LoopGuard()
    fp = _fp()
    assert guard.fingerprint(fp) == guard.fingerprint(fp)


# ── is_looping semantics ──────────────────────────────────────────────


def test_is_looping_triggers_on_threshold_th_occurrence() -> None:
    guard = LoopGuard(window=5, threshold=3)
    fp = _fp()
    # 1st + 2nd occurrences must not trigger.
    assert guard.is_looping(fp) is False
    assert guard.is_looping(fp) is False
    # 3rd occurrence == threshold -> trigger.
    assert guard.is_looping(fp) is True


def test_is_looping_distinct_fingerprints_do_not_accumulate() -> None:
    guard = LoopGuard(window=5, threshold=2)
    a = _fp(target="a.py")
    b = _fp(target="b.py")
    assert guard.is_looping(a) is False
    assert guard.is_looping(b) is False
    # Second a — threshold=2 met for a but only once each so far.
    assert guard.is_looping(a) is True


def test_is_looping_respects_window_eviction() -> None:
    # window=2 means only the last 2 entries are retained. A third
    # occurrence of the same fingerprint separated by two others must
    # therefore NOT trigger.
    guard = LoopGuard(window=2, threshold=2)
    a = _fp(target="a.py")
    b = _fp(target="b.py")
    guard.is_looping(a)   # history: [a]
    guard.is_looping(b)   # history: [a, b]
    guard.is_looping(b)   # history: [b, b] -> loop on b, but we test a next
    assert guard.is_looping(a) is False  # history: [b, a] -> only 1 a


def test_threshold_of_one_triggers_immediately() -> None:
    guard = LoopGuard(window=5, threshold=1)
    assert guard.is_looping(_fp()) is True


# ── reset ─────────────────────────────────────────────────────────────


def test_reset_clears_history() -> None:
    guard = LoopGuard(window=5, threshold=2)
    fp = _fp()
    guard.is_looping(fp)
    guard.reset()
    # Post-reset, first sighting must not trigger.
    assert guard.is_looping(fp) is False


# ── suggest_escalation ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "approach,expected",
    [
        ("syntax", "structural"),
        ("structural", "rewrite"),
        ("rewrite", "delegate_to_human"),
        ("logic", "delegate_to_human"),  # unmapped -> fallback
        ("unknown_bucket", "delegate_to_human"),
    ],
)
def test_suggest_escalation(approach: str, expected: str) -> None:
    guard = LoopGuard()
    assert guard.suggest_escalation(_fp(approach=approach)) == expected


# ── defaults ──────────────────────────────────────────────────────────


def test_default_window_and_threshold() -> None:
    guard = LoopGuard()
    assert guard.history.maxlen == 5
    assert guard.threshold == 3
