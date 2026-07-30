"""adapters.memory.dozerdb.amg_v02_policy — Real AMG v0.2.2 AmgPolicy (ADR-027, ADR-047).

Wraps `agent_memory_guard` v0.2.2 as the write-time policy filter behind the
`AmgPolicy` Protocol. Satisfies `AmgPolicy.evaluate(payload) -> AmgVerdict`
from `adapters.memory.dozerdb.adapter`.

## v0.2.2 API limitation

AMG v0.2.2's public surface exposes a policy *executor* (`guard.write`) rather
than a pure evaluator. `guard.write` either returns (allow / redact /
quarantine internally) or raises `PolicyViolation` (block). Redact and
quarantine outcomes are folded into the store and are not distinguishable
from `allow` via the public API in v0.2.2.

We therefore implement `evaluate` as a snapshot-execute-rollback pattern:

1. `snap = guard.snapshot(label="pre-evaluate")`
2. `guard.write(key, value)` inside a try
3. On `PolicyViolation` → `AmgVerdict(decision="block", reason=str(exc))`
4. Otherwise → `AmgVerdict(decision="allow")`
5. Always `guard.rollback(snap.snapshot_id)` so `evaluate` is side-effect-free

Once agent-memory-guard v0.3.0 ships a pure `Policy.evaluate` API (Stage 4.3
per Kosmos-Build-Sequence-v25.md §4.3), replace this wrapper with a direct
evaluator that can distinguish redact + quarantine cleanly.

All `agent_memory_guard` imports are lazy so the fast unit tier does not
require the package to be importable.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from adapters.memory.dozerdb.adapter import AmgVerdict

log = logging.getLogger(__name__)


class AmgV02Policy:
    """AMG v0.2.2 policy wrapper implementing `AmgPolicy`.

    Constructor takes an optional YAML policy path. If omitted, uses
    `Policy.strict()`. The underlying `MemoryGuard` is built lazily on first
    `evaluate` call so init failure does not blow up the adapter at
    construction time.

    Contract tests exercise this class with a mocked `MemoryGuard`. Env-gated
    live tier (KOSMOS_STAGE_42_LIVE=1) runs against real AMG.
    """

    def __init__(self, policy_yaml_path: Path | None = None) -> None:
        self._policy_yaml_path = policy_yaml_path
        self._guard: Any | None = None
        self._init_error: str | None = None

    def evaluate(self, payload: dict[str, Any]) -> AmgVerdict:
        try:
            guard = self._ensure_guard()
        except Exception as e:  # noqa: BLE001
            # Fail-safe: policy init failure blocks the write. Zero-trust
            # (spec §7) — never treat a broken guard as permissive.
            log.warning("AmgV02Policy: guard init failed, blocking: %s", e)
            return AmgVerdict(
                decision="block",
                reason=f"amg-init-failed: {type(e).__name__}: {e}",
            )

        key, value = self._payload_to_kv(payload)

        # Lazy import for the exception type.
        from agent_memory_guard import PolicyViolation

        try:
            snap = guard.snapshot(label="pre-evaluate")
        except Exception as e:  # noqa: BLE001 — snapshot is best-effort
            log.warning(
                "AmgV02Policy: snapshot failed, evaluate becomes side-effectful: %s",
                e,
            )
            snap = None

        try:
            guard.write(key, value)
            verdict = AmgVerdict(decision="allow")
        except PolicyViolation as exc:
            verdict = AmgVerdict(
                decision="block",
                reason=str(exc) or "policy-violation",
            )
        except Exception as e:  # noqa: BLE001 — treat unknown errors as block
            log.warning(
                "AmgV02Policy: guard.write raised %s, blocking as fail-safe",
                type(e).__name__,
            )
            verdict = AmgVerdict(
                decision="block",
                reason=f"amg-write-failed: {type(e).__name__}: {e}",
            )

        # Roll back regardless of outcome so evaluate() stays side-effect-free.
        if snap is not None:
            try:
                snap_id = getattr(snap, "snapshot_id", snap)
                guard.rollback(snap_id)
            except Exception as e:  # noqa: BLE001
                log.warning(
                    "AmgV02Policy: rollback swallowed error %s: %s",
                    type(e).__name__,
                    e,
                )

        return verdict

    # ── internal ────────────────────────────────────────────────────────────

    def _ensure_guard(self) -> Any:
        if self._guard is not None:
            return self._guard
        # Lazy imports — module-level would drag agent_memory_guard into the
        # fast unit tier.
        from agent_memory_guard import MemoryGuard, Policy

        if self._policy_yaml_path is not None:
            from agent_memory_guard.policies.policy import load_policy

            policy = load_policy(Path(self._policy_yaml_path))
        else:
            policy = Policy.strict()
        self._guard = MemoryGuard(policy=policy)
        return self._guard

    @staticmethod
    def _payload_to_kv(payload: dict[str, Any]) -> tuple[str, str]:
        """Map a MemoryPort payload to an AMG (key, value) pair.

        AMG operates on key/value writes; the adapter operates on typed
        triples + arbitrary payload dicts. We derive:
        - `key` from `subject` / `source_id` / `id`, else `memory.event`
        - `value` = deterministic JSON serialization of `payload`
        """
        key = str(
            payload.get("subject")
            or payload.get("source_id")
            or payload.get("id")
            or "memory.event"
        )
        value = json.dumps(payload, default=str, sort_keys=True)
        return key, value
