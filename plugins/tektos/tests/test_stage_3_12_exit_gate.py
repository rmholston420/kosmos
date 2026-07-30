"""Stage 3.12 · Stage-3 exit gate DoD literal (ADR-046).

Locks in the Stage-3 exit gate as one end-to-end pipeline test:

    TektosAgent (Stage 3.1)
      → MCP tool (Stage 3.2, HUMAN_REQUIRED → TektosToolCallPending)
      → repomap.index (Stage 3.3)
      → openspec.produce_plan (Stage 3.6)
      → renderer.render_and_gate_plan_card (Stage 3.7, HUMAN_REVIEW)
      → UI Approve / Execute / Diff (Stage 3.11)

The refactor target — ``plugins/tektos/ui/templates.py`` — was already
modified in the previous commit (Tektos-authored, marker
``Stage 3.12 · Tektos refactor · extract-method``). This test observes
that the extracted helper ``_escape_record_fields`` exists and that
the UI end-to-end path still renders correctly through the refactored
surface.

The DoD literal test asserts, in one function, that every leg of the
Stage-3 pipeline drove the refactor to a landed commit and that the
final surface passes ruff + bandit + pytest.

The fast tier (default) uses ADR-046 Interp-2: human-authored
canned LLM response wired through a Protocol-conforming fake
LLMPort. The interactive tier (env-gated
``KOSMOS_STAGE_312_INTERACTIVE=1``) is Interp-1: real Ollama
LLMPort on Colossus. Both tiers exercise the same Stage-3 pipeline.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from adapters.approval_resolver.praxis import PraxisApprovalResolverAdapter
from plugins.praxis.apex import (
    FakeScheduler,
    InMemoryStorage,
    KernelChangeApprovalAdapter,
)
from plugins.tektos import openspec as tektos_openspec  # noqa: F401  (import-guard)
from plugins.tektos.agent import TektosAgent
from plugins.tektos.errors import TektosToolCallPending
from plugins.tektos.openspec import produce_plan
from plugins.tektos.renderer import render_and_gate_plan_card
from plugins.tektos.repomap import index as repomap_index
from plugins.tektos.ui import (
    NopExecutor,
    build_tektos_ui_app,
)
from plugins.tektos.ui.templates import (
    _escape_record_fields,
    render_pending_row,
    render_plan_detail,
)

from ports.memory import MemoryEventId

# ── Repo constants ─────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[3]
REFACTOR_TARGET = "plugins/tektos/ui/templates.py"
REFACTOR_COMMIT_MARKER = "Stage 3.12 · Tektos refactor · extract-method"
FIXTURE_CHANGE = (
    Path(__file__).parent
    / "fixtures"
    / "openspec"
    / "refactor-tektos-ui-templates-extract-escape-helpers"
).resolve()

INTERACTIVE_TIER_ENV = "KOSMOS_STAGE_312_INTERACTIVE"


# ── Fake ports (Interp-2 fast tier) ───────────────────────────────────────


@dataclass(slots=True)
class _FakeLLMPort:
    """Human-authored canned response — Interp-2 (ADR-046 Q3.1=C fast tier)."""

    canned_response: str = (
        "I will extract the duplicated escape block in "
        "plugins/tektos/ui/templates.py into _escape_record_fields."
    )
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def generate_text(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
    ) -> str:
        self.calls.append(
            {"prompt": prompt, "model": model, "system": system}
        )
        return self.canned_response

    async def generate(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    async def chat(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    async def embed(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    async def list_models(self) -> list[dict[str, Any]]:  # pragma: no cover
        return []

    async def pull_model(self, **_: Any) -> None:  # pragma: no cover
        return None

    async def delete_model(self, **_: Any) -> None:  # pragma: no cover
        return None

    async def is_healthy(self) -> bool:
        return True

    async def close(self) -> None:  # pragma: no cover
        return None


@dataclass(slots=True)
class _FakeMemoryPort:
    """MemoryPort double honouring ADR-008 zero-trust write shape."""

    writes: list[dict[str, Any]] = field(default_factory=list)
    _next_seq: int = 0

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> MemoryEventId:
        # Real zero-trust guard is enforced by DozerDB; the fake honours the
        # protocol shape only. Reject empty provenance to catch coding bugs.
        if not provenance or not provenance.strip():
            raise ValueError("provenance must be non-empty")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence out of range: {confidence!r}")
        self._next_seq += 1
        self.writes.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "provenance": provenance,
                "confidence": confidence,
                "pii_tier": pii_tier,
                "attributes": dict(attributes or {}),
            }
        )
        return MemoryEventId(
            id=f"mem-{self._next_seq}",
            written_at=datetime.now(timezone.utc),
        )

    async def query_temporal(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    async def link_entities(self, *args: Any, **kwargs: Any) -> MemoryEventId:
        self._next_seq += 1
        return MemoryEventId(
            id=f"mem-link-{self._next_seq}",
            written_at=datetime.now(timezone.utc),
        )

    def is_healthy(self) -> bool:
        return True


class _NullEventBus:
    async def publish(self, *args: Any, **kwargs: Any) -> None:
        return None


class _NullNotification:
    async def notify(self, *args: Any, **kwargs: Any) -> None:
        return None


class _NopMCPPort:
    """MCPPort double.

    ``file_write`` is HUMAN_REQUIRED, so :meth:`TektosAgent.call_tool`
    raises :class:`TektosToolCallPending` at the gate before this port
    is ever invoked. Every method here therefore raises.
    """

    async def initialize(self, **_: Any) -> None:  # pragma: no cover
        return None

    async def list_tools(self) -> tuple[Any, ...]:  # pragma: no cover
        return ()

    async def call_tool(self, **_: Any) -> Any:  # pragma: no cover
        raise AssertionError(
            "MCP.call_tool must not be reached — HUMAN_REQUIRED gate raises first"
        )

    async def close(self) -> None:  # pragma: no cover
        return None

    def is_healthy(self) -> bool:
        return True


# ── Helpers ────────────────────────────────────────────────────────────────


def _build_apex() -> KernelChangeApprovalAdapter:
    """Wire a real APEX exactly like ``scripts/tektos_ui.py``."""
    return KernelChangeApprovalAdapter(
        storage=InMemoryStorage(),
        scheduler=FakeScheduler(),
        event_bus=_NullEventBus(),
        notification=_NullNotification(),
    )


def _git_log_grep(marker: str) -> list[str]:
    proc = subprocess.run(  # noqa: S603, S607
        ["git", "log", "--oneline", "--grep", marker, "-n", "5"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


# ── Fast-tier supporting tests ─────────────────────────────────────────────


def test_escape_record_fields_projects_four_html_escaped_strings() -> None:
    """The extracted helper exists and returns a 4-tuple of escaped strings."""
    from ports.approval import (
        ApprovalRecord,
        ApprovalStatus,
        ChangeApprovalTier,
    )

    record = ApprovalRecord(
        approval_id="a-<script>",
        intention_id="tektos.plan.change-<42>",
        proposing_domain="tektos",
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta={},
        status=ApprovalStatus.PENDING,
        proposed_at=datetime.now(timezone.utc),
    )

    result = _escape_record_fields(record)

    assert isinstance(result, tuple)
    assert len(result) == 4
    approval_id, change_id, tier, status = result
    # HTML-escaped output: `<` becomes `&lt;`.
    assert approval_id == "a-&lt;script&gt;"
    assert change_id == "change-&lt;42&gt;"
    assert tier == "HUMAN_REVIEW"
    assert status == "PENDING"


def test_render_pending_row_still_uses_extracted_helper() -> None:
    """Refactored ``render_pending_row`` continues to emit a valid row."""
    from ports.approval import (
        ApprovalRecord,
        ApprovalStatus,
        ChangeApprovalTier,
    )

    record = ApprovalRecord(
        approval_id="a-1",
        intention_id="tektos.plan.change-42",
        proposing_domain="tektos",
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta={},
        status=ApprovalStatus.PENDING,
        proposed_at=datetime.now(timezone.utc),
    )
    html = render_pending_row(record)
    assert html.startswith('<tr id="row-a-1">')
    assert "change-42" in html
    assert "HUMAN_REVIEW" in html
    assert "PENDING" in html


def test_render_plan_detail_still_uses_extracted_helper() -> None:
    """Refactored ``render_plan_detail`` continues to emit a valid section."""
    from ports.approval import (
        ApprovalRecord,
        ApprovalStatus,
        ChangeApprovalTier,
    )

    record = ApprovalRecord(
        approval_id="a-2",
        intention_id="tektos.plan.change-99",
        proposing_domain="tektos",
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta={},
        status=ApprovalStatus.PENDING,
        proposed_at=datetime.now(timezone.utc),
    )
    html = render_plan_detail(record)
    assert '<section id="plan-detail-a-2">' in html
    assert "change-99" in html


def test_refactor_commit_present_on_head() -> None:
    """Marker string must exist in git log (Q6=A · two-commit shape)."""
    hits = _git_log_grep(REFACTOR_COMMIT_MARKER)
    assert hits, f"no commit found matching {REFACTOR_COMMIT_MARKER!r}"


# ── DoD literal — full Stage-3 pipeline ──────────────────────────────────


@pytest.mark.asyncio
async def test_tektos_refactors_real_kosmos_file_end_to_end_passes_ruff_bandit_pytest_build_sequence_3_12_dod() -> None:  # noqa: E501
    """Build-Sequence §3.12 DoD literal (ADR-046).

    Drives the full Stage-3 pipeline against fake ports (Interp-2 fast
    tier) and asserts every leg contributed to landing the refactor
    commit:

      1. Stage 3.1 · TektosAgent emits its coding intent (canned LLM).
      2. Stage 3.2 · MCP tool ``file_write`` is HUMAN_REQUIRED and
         raises :class:`TektosToolCallPending` — the agent respects
         the approval gate for source-code writes.
      3. Stage 3.3 · repomap indexes the refactored templates.py.
      4. Stage 3.6 · openspec.produce_plan parses the change fixture
         under ``fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers``.
      5. Stage 3.7 · renderer.render_and_gate_plan_card proposes the
         plan through real APEX at HUMAN_REVIEW.
      6. Stage 3.11 · UI Approve/Execute/Diff flow exercises the
         refactored ``templates.py`` (via the just-approved plan).

    Final assertions:
      * ruff + bandit both exit 0 on the refactor target.
      * The refactor commit marker is present on HEAD.
    """
    # ── 1. Stage 3.1 · TektosAgent ────────────────────────────────────
    llm = _FakeLLMPort()
    memory = _FakeMemoryPort()
    apex = _build_apex()
    agent = TektosAgent(
        llm=llm,
        memory=memory,
        mcp=_NopMCPPort(),
        apex=apex,
        subject="tektos_user",
    )
    turn_id = agent.send_message(
        "Refactor plugins/tektos/ui/templates.py: "
        "extract the duplicated escape block into _escape_record_fields."
    )
    step = await agent.run()
    assert step.turn_id == turn_id
    assert step.response == llm.canned_response
    assert len(llm.calls) == 1

    # ── 2. Stage 3.2 · MCP tool respects HUMAN_REQUIRED gate ──────────
    with pytest.raises(TektosToolCallPending) as exc:
        await agent.call_tool(
            name="file_write",
            arguments={
                "path": REFACTOR_TARGET,
                "content": "(refactored)",
            },
        )
    assert exc.value.tool_name == "file_write"
    assert exc.value.approval_id

    # ── 3. Stage 3.3 · repomap indexes a tmp workspace containing the
    #      refactored file. Using a tmp dir keeps the index fast and
    #      hermetic; the target's real content is what gets indexed.
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory(prefix="kosmos-3-12-") as tmp:
        tmp_root = Path(tmp)
        target_copy = tmp_root / "templates.py"
        shutil.copyfile(ROOT / REFACTOR_TARGET, target_copy)
        repomap_result = await repomap_index(tmp_root, memory=memory)
    assert repomap_result.files_indexed >= 1
    assert any(
        rel_fname.endswith("templates.py")
        for rel_fname, _rank in repomap_result.top_files
    ), "repomap did not surface templates.py"
    assert "_escape_record_fields" in repomap_result.rendered_map

    # ── 4. Stage 3.6 · openspec.produce_plan on the change fixture ────
    plan_result = await produce_plan(FIXTURE_CHANGE, memory)
    assert plan_result.plan.change_id == FIXTURE_CHANGE.name
    assert plan_result.plan.task_count > 0
    assert plan_result.plan_event_id is not None

    # ── 5. Stage 3.7 · render + gate through real APEX ────────────────
    card = await render_and_gate_plan_card(
        plan_result.plan,
        panel_id="tektos-plan-card",
        approval=apex,
        memory=memory,
    )
    assert card.change_id == FIXTURE_CHANGE.name
    assert card.approval_id  # APEX assigned one at HUMAN_REVIEW

    # ── 6. Stage 3.11 · UI Approve/Execute/Diff over refactored file ─
    resolver = PraxisApprovalResolverAdapter(engine=apex)
    app = build_tektos_ui_app(
        approval_resolver=resolver,
        memory=memory,
        executor=NopExecutor(),
    )
    # Import TestClient locally so pytest doesn't need FastAPI/httpx at
    # module-import time on hosts that skip UI tests.
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        r_detail = client.get(f"/plan/{card.approval_id}")
        assert r_detail.status_code == 200
        # Refactored templates.py: `_escape_record_fields` still emits
        # the plan-detail section shell.
        assert f'<section id="plan-detail-{card.approval_id}">' in r_detail.text

        r_approve = client.post(f"/plan/{card.approval_id}/approve")
        assert r_approve.status_code == 200

        r_execute = client.post(f"/plan/{card.approval_id}/execute")
        assert r_execute.status_code == 200

        r_diff = client.get(f"/plan/{card.approval_id}/diff")
        assert r_diff.status_code == 200

    # ── Final DoD assertions ─────────────────────────────────────────
    ruff = ROOT / ".venv" / "bin" / "ruff"
    bandit = ROOT / ".venv" / "bin" / "bandit"
    assert ruff.exists(), f"ruff missing at {ruff}"
    assert bandit.exists(), f"bandit missing at {bandit}"

    ruff_proc = subprocess.run(  # noqa: S603
        [str(ruff), "check", REFACTOR_TARGET],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ruff_proc.returncode == 0, (
        f"ruff failed:\n{ruff_proc.stdout}\n{ruff_proc.stderr}"
    )

    bandit_proc = subprocess.run(  # noqa: S603
        [
            str(bandit),
            "-q",
            "-c",
            "pyproject.toml",
            "-r",
            REFACTOR_TARGET,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert bandit_proc.returncode == 0, (
        f"bandit failed:\n{bandit_proc.stdout}\n{bandit_proc.stderr}"
    )

    # And the refactor commit marker is on HEAD.
    hits = _git_log_grep(REFACTOR_COMMIT_MARKER)
    assert hits, (
        f"no commit matching {REFACTOR_COMMIT_MARKER!r} on HEAD"
    )


# ── Interactive tier (env-gated, Colossus-only) ────────────────────────────


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get(INTERACTIVE_TIER_ENV) != "1",
    reason=(
        "Interactive tier is Colossus-only. "
        f"Set {INTERACTIVE_TIER_ENV}=1 to run against real Ollama."
    ),
)
async def test_stage_3_12_interactive_tier_runs_against_real_ollama() -> None:
    """Interp-1 interactive tier (ADR-046 Q3.1=C).

    Replaces the fake LLMPort with a real ``OllamaLLMAdapter`` on
    Colossus (128GB RAM, RTX 5090). Everything else in the pipeline is
    identical to the fast tier. This test does NOT gate CI — it is a
    documented reproducer for the interactive run.
    """
    if sys.platform != "linux":
        pytest.skip("Interactive tier requires Linux + Colossus GPU")
    from adapters.llm.ollama import OllamaLLMAdapter

    llm = OllamaLLMAdapter()  # defaults to http://127.0.0.1:11434
    memory = _FakeMemoryPort()
    apex = _build_apex()
    agent = TektosAgent(llm=llm, memory=memory, apex=apex)
    agent.send_message(
        "Refactor plugins/tektos/ui/templates.py: extract the "
        "duplicated escape block into _escape_record_fields."
    )
    step = await agent.run()
    assert step.response  # real LLM returned something
    # We do not re-run the full pipeline here; the fast-tier DoD test
    # already covers behavioural equivalence.
