"""adapters.memory.dozerdb.amg_policy — Real AMG v0.3.0 AmgPolicy (ADR-027, ADR-047, ADR-048).

Wraps `agent_memory_guard` v0.3.0 as the write-time policy filter behind the
`AmgPolicy` Protocol from `adapters.memory.dozerdb.adapter`.

## v0.3.0 changes vs v0.2.2

- Default policy is `Policy.tiered()` (new memory-class taxonomy shipped in
  v0.3.0, PR #23) so this adapter honours the layered promotion model instead
  of the flat strict-only ruleset. Pass an explicit `policy_yaml_path` or the
  `policy_preset` kwarg to override.
- `MemoryGuard.write` now accepts optional `source_class`, `receipt_uri`, and
  `cls` kwargs. We surface `source_class` to callers via `evaluate(payload)`
  — a `payload["source_class"]` (`SourceClass` enum or string like
  "agent_authored" / "external_tool" / "user_input") is forwarded verbatim
  and defaults to `AGENT_AUTHORED` when omitted.
- The public API is otherwise a strict superset of v0.2.2. The
  snapshot-execute-rollback evaluation pattern from v0.2.2 is preserved —
  v0.3.0 still lacks a pure `Policy.evaluate` surface (that ships post-0.3.0
  per upstream roadmap; when it lands we replace this wrapper).

## Zero-trust fail-safe (spec §7 · ADR-008)

- Guard init failure → `AmgVerdict(decision="block")`. Never permissive.
- Unknown `guard.write` error → block. Never permissive.
- Snapshot failure → best-effort; evaluate still runs but `rollback` is
  skipped and a WARN is logged so operators see the leaked write.

## Backwards compatibility

`AmgV02Policy` is retained as a module-level alias for
`AmgGuardPolicy` for one release cycle so downstream callers importing
`from adapters.memory.dozerdb import AmgV02Policy` keep working. Remove at
Stage 5.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from adapters.memory.dozerdb.adapter import AmgVerdict

log = logging.getLogger(__name__)


class AmgGuardPolicy:
    """AMG v0.3.0 policy wrapper implementing the `AmgPolicy` Protocol.

    Args:
        policy_yaml_path: Optional YAML policy file loaded via
            `agent_memory_guard.policies.policy.load_policy`. Overrides
            `policy_preset` when set.
        policy_preset: One of `"tiered"` (default) or `"strict"`. Selects
            the built-in `Policy.tiered()` (v0.3.0) or `Policy.strict()`
            (v0.2.2-compatible) baseline. Ignored when `policy_yaml_path`
            is provided.

    The underlying `MemoryGuard` is built lazily on the first `evaluate`
    call so init failure does not blow up the adapter at construction
    time.
    """

    def __init__(
        self,
        policy_yaml_path: Path | None = None,
        *,
        policy_preset: str = "tiered",
    ) -> None:
        self._policy_yaml_path = policy_yaml_path
        self._policy_preset = policy_preset
        self._guard: Any | None = None

    def evaluate(self, payload: dict[str, Any]) -> AmgVerdict:
        try:
            guard = self._ensure_guard()
        except Exception as e:  # noqa: BLE001
            # Fail-safe: policy init failure blocks the write. Zero-trust
            # (spec §7) — never treat a broken guard as permissive.
            log.warning("AmgGuardPolicy: guard init failed, blocking: %s", e)
            return AmgVerdict(
                decision="block",
                reason=f"amg-init-failed: {type(e).__name__}: {e}",
            )

        key, value = self._payload_to_kv(payload)
        write_kwargs = self._payload_to_write_kwargs(payload)

        # Lazy import for the exception type.
        from agent_memory_guard import PolicyViolation

        try:
            snap = guard.snapshot(label="pre-evaluate")
        except Exception as e:  # noqa: BLE001 — snapshot is best-effort
            log.warning(
                "AmgGuardPolicy: snapshot failed, evaluate becomes side-effectful: %s",
                e,
            )
            snap = None

        try:
            guard.write(key, value, **write_kwargs)
            verdict = AmgVerdict(decision="allow")
        except PolicyViolation as exc:
            verdict = AmgVerdict(
                decision="block",
                reason=str(exc) or "policy-violation",
            )
        except Exception as e:  # noqa: BLE001 — treat unknown errors as block
            log.warning(
                "AmgGuardPolicy: guard.write raised %s, blocking as fail-safe",
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
                    "AmgGuardPolicy: rollback swallowed error %s: %s",
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
        elif self._policy_preset == "strict":
            policy = Policy.strict()
        elif self._policy_preset == "tiered":
            policy = Policy.tiered()
        else:
            raise ValueError(
                f"unknown policy_preset {self._policy_preset!r}; "
                "expected 'tiered' or 'strict'"
            )
        self._guard = MemoryGuard(policy=policy)
        return self._guard

    # ── ADR-076 D6 accessors (read-only, no state mutation) ─────────────────

    @property
    def policy_preset(self) -> str:
        """The active policy preset name ("tiered" | "strict" | ...).

        Returns ``"custom-yaml"`` when constructed from a YAML file.
        """
        if self._policy_yaml_path is not None:
            return "custom-yaml"
        return self._policy_preset

    def active_detectors(self) -> list[str]:
        """List of detector names from AMG's own detector registry.

        Wraps ``guard._policy.detectors.keys()`` — sourced from AMG, not
        hard-coded. Returns ``[]`` if the guard has not been built yet or
        if AMG's policy shape lacks a ``detectors`` mapping.
        """
        try:
            guard = self._ensure_guard()
        except Exception:  # noqa: BLE001
            return []
        policy = getattr(guard, "_policy", None) or getattr(guard, "policy", None)
        if policy is None:
            return []
        detectors = getattr(policy, "detectors", None)
        if detectors is None:
            return []
        try:
            keys = list(detectors.keys())
        except AttributeError:
            try:
                keys = [str(d) for d in detectors]
            except TypeError:
                return []
        return [str(k) for k in keys]

    @staticmethod
    def _payload_to_kv(payload: dict[str, Any]) -> tuple[str, str]:
        """Map a MemoryPort payload to an AMG (key, value) pair.

        AMG operates on key/value writes; the adapter operates on typed
        triples + arbitrary payload dicts. We derive:
        - `key` from `subject` / `source_id` / `id`, else `memory.event`
        - `value` = deterministic JSON serialization of `payload`
          (excluding AMG-only routing fields so `value` remains the
          semantic body of the write)
        """
        key = str(
            payload.get("subject")
            or payload.get("source_id")
            or payload.get("id")
            or "memory.event"
        )
        body = {
            k: v
            for k, v in payload.items()
            if k not in _AMG_ROUTING_KEYS
        }
        value = json.dumps(body, default=str, sort_keys=True)
        return key, value

    @staticmethod
    def _payload_to_write_kwargs(payload: dict[str, Any]) -> dict[str, Any]:
        """Extract v0.3.0 `MemoryGuard.write` kwargs from the payload.

        Recognised routing fields (all optional):
        - `source_class` — `SourceClass` enum or string identifier
        - `receipt_uri` — external audit-receipt URI
        - `memory_class` / `cls` — provenance class for classification
        - `task_id` — cross-task check override
        - `source` — writer identifier (defaults to AMG's `"agent"`)
        """
        kwargs: dict[str, Any] = {}
        if "source_class" in payload:
            kwargs["source_class"] = payload["source_class"]
        if "receipt_uri" in payload:
            kwargs["receipt_uri"] = payload["receipt_uri"]
        if "memory_class" in payload:
            kwargs["cls"] = payload["memory_class"]
        elif "cls" in payload:
            kwargs["cls"] = payload["cls"]
        if "task_id" in payload:
            kwargs["task_id"] = payload["task_id"]
        if "source" in payload:
            kwargs["source"] = payload["source"]
        return kwargs


_AMG_ROUTING_KEYS = frozenset(
    {"source_class", "receipt_uri", "memory_class", "cls", "task_id", "source"}
)


# Backwards-compat alias (removed at Stage 5). See ADR-048.
AmgV02Policy = AmgGuardPolicy
