"""Stage 3.13 DoD contract tests for the intention scaffolder (ADR-077).

Coverage:

* Locked constants (policy.py) — provenance, predicate, env var, bounds.
* Slug helper — deterministic, unicode-safe, empty-slug rejection.
* Root resolution — env override, XDG fallback, home fallback.
* Scaffold happy path — creates proposal.md + tasks.md, parses via
  ``openspec.walk_change_directory``.
* Scaffold length guards — reject too-short and too-long intentions.
* Scaffold idempotency guard — refuse to overwrite existing directory.
* ADR-007 no-cross-plugin-import guard (AST verified).

Zero third-party imports required.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest

from plugins.tektos.intention import (
    INTENTION_PROVENANCE,
    INTENTION_ROOT_ENV,
    INTENTION_SCAFFOLD_PREDICATE,
    INTENTION_WRITE_CONFIDENCE,
    MAX_INTENTION_LENGTH,
    MIN_INTENTION_LENGTH,
    IntentionScaffoldError,
    ScaffoldResult,
    intention_to_change_id,
    resolve_intention_root,
    scaffold_intention,
)

# ── Locked constants ────────────────────────────────────────────────────────


def test_intention_provenance_locked() -> None:
    assert INTENTION_PROVENANCE == "tektos_intention_scaffolder"


def test_intention_predicate_locked() -> None:
    assert INTENTION_SCAFFOLD_PREDICATE == "tektos.intention.scaffolded"


def test_intention_root_env_locked() -> None:
    assert INTENTION_ROOT_ENV == "KOSMOS_TEKTOS_INTENTION_ROOT"


def test_intention_write_confidence_locked() -> None:
    assert INTENTION_WRITE_CONFIDENCE == 1.0


def test_intention_length_bounds_locked() -> None:
    assert MIN_INTENTION_LENGTH == 8
    assert MAX_INTENTION_LENGTH == 512
    assert MIN_INTENTION_LENGTH < MAX_INTENTION_LENGTH


# ── Slug helper ─────────────────────────────────────────────────────────────


def test_slug_basic() -> None:
    assert intention_to_change_id("Add dark mode") == "add-dark-mode"


def test_slug_strips_whitespace_and_lowercases() -> None:
    assert intention_to_change_id("   Add DARK Mode   ") == "add-dark-mode"


def test_slug_removes_punctuation() -> None:
    assert intention_to_change_id("Fix bug #42: crash!") == "fix-bug-42-crash"


def test_slug_collapses_hyphen_runs() -> None:
    assert intention_to_change_id("a---b   c") == "a-b-c"


def test_slug_nfkd_normalizes_diacritics() -> None:
    assert intention_to_change_id("Café résumé") == "cafe-resume"


def test_slug_truncates_to_max_length() -> None:
    long = "word " * 40
    slug = intention_to_change_id(long)
    assert len(slug) <= 48
    assert not slug.endswith("-")


def test_slug_rejects_non_string() -> None:
    with pytest.raises(IntentionScaffoldError):
        intention_to_change_id(None)  # type: ignore[arg-type]


def test_slug_rejects_whitespace_only() -> None:
    with pytest.raises(IntentionScaffoldError):
        intention_to_change_id("   ")


def test_slug_rejects_all_hyphen() -> None:
    with pytest.raises(IntentionScaffoldError):
        intention_to_change_id("---")


def test_slug_rejects_unicode_only() -> None:
    # Emoji NFKD-normalizes to something ascii-strippable to empty.
    with pytest.raises(IntentionScaffoldError):
        intention_to_change_id("🚀🚀🚀")


# ── Root resolution ─────────────────────────────────────────────────────────


def test_resolve_root_respects_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(INTENTION_ROOT_ENV, str(tmp_path / "custom"))
    root = resolve_intention_root()
    assert root == (tmp_path / "custom").resolve()


def test_resolve_root_falls_back_to_xdg_state_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(INTENTION_ROOT_ENV, raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    root = resolve_intention_root()
    assert root == (tmp_path / "kosmos" / "tektos" / "intentions").resolve()


def test_resolve_root_home_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(INTENTION_ROOT_ENV, raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    root = resolve_intention_root()
    expected = (
        Path.home() / ".local" / "state" / "kosmos" / "tektos" / "intentions"
    ).resolve()
    assert root == expected


def test_env_override_beats_xdg(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(INTENTION_ROOT_ENV, str(tmp_path / "explicit"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    assert resolve_intention_root() == (tmp_path / "explicit").resolve()


# ── Scaffold happy path ─────────────────────────────────────────────────────


def test_scaffold_creates_valid_openspec_change_dir(tmp_path: Path) -> None:
    result = scaffold_intention("Add dark mode toggle to settings", root=tmp_path)

    assert isinstance(result, ScaffoldResult)
    assert result.change_id == "add-dark-mode-toggle-to-settings"
    assert result.change_dir == (tmp_path / result.change_id).resolve()
    assert result.change_dir.is_dir()

    proposal = (result.change_dir / "proposal.md").read_text()
    assert "Add dark mode toggle to settings" in proposal
    assert "## Why" in proposal
    assert "## What Changes" in proposal

    tasks = (result.change_dir / "tasks.md").read_text()
    assert "Refine" in tasks


def test_scaffold_parseable_by_openspec_walker(tmp_path: Path) -> None:
    from plugins.tektos.openspec.parser import walk_change_directory

    result = scaffold_intention(
        "Add dark mode toggle to the settings panel", root=tmp_path
    )
    found = walk_change_directory(result.change_dir)

    assert "proposal.md" in found
    assert "tasks.md" in found


def test_scaffold_uses_injected_timestamp(tmp_path: Path) -> None:
    ts = datetime(2026, 8, 1, 20, 0, 0, tzinfo=UTC)
    result = scaffold_intention(
        "Add dark mode toggle to settings", root=tmp_path, now=ts
    )
    assert result.scaffolded_at == ts
    assert "2026-08-01T20:00:00+00:00" in (
        result.change_dir / "proposal.md"
    ).read_text()


def test_scaffold_default_timestamp_is_timezone_aware(tmp_path: Path) -> None:
    result = scaffold_intention(
        "Add dark mode toggle to settings", root=tmp_path
    )
    assert result.scaffolded_at.tzinfo is not None


# ── Scaffold length guards ──────────────────────────────────────────────────


def test_scaffold_rejects_too_short(tmp_path: Path) -> None:
    with pytest.raises(IntentionScaffoldError, match="too short"):
        scaffold_intention("short", root=tmp_path)


def test_scaffold_rejects_too_long(tmp_path: Path) -> None:
    with pytest.raises(IntentionScaffoldError, match="too long"):
        scaffold_intention("x" * (MAX_INTENTION_LENGTH + 1), root=tmp_path)


def test_scaffold_rejects_non_string(tmp_path: Path) -> None:
    with pytest.raises(IntentionScaffoldError):
        scaffold_intention(None, root=tmp_path)  # type: ignore[arg-type]


def test_scaffold_accepts_exactly_min_length(tmp_path: Path) -> None:
    # MIN=8; slug must survive slugification.
    result = scaffold_intention("abcdefgh", root=tmp_path)
    assert result.change_id == "abcdefgh"


def test_scaffold_strips_before_length_check(tmp_path: Path) -> None:
    # "  hello  " strips to "hello" (5 < MIN=8) — must reject.
    with pytest.raises(IntentionScaffoldError, match="too short"):
        scaffold_intention("  hello  ", root=tmp_path)


# ── Scaffold idempotency ────────────────────────────────────────────────────


def test_scaffold_refuses_to_overwrite(tmp_path: Path) -> None:
    scaffold_intention("Add dark mode toggle to settings", root=tmp_path)
    with pytest.raises(IntentionScaffoldError, match="already exists"):
        scaffold_intention("Add dark mode toggle to settings", root=tmp_path)


# ── ADR-007 guard ───────────────────────────────────────────────────────────


def test_intention_module_does_not_import_other_plugins() -> None:
    """ADR-007: no plugin imports another plugin's package."""
    from plugins.tektos import intention as mod
    root = Path(inspect.getfile(mod)).parent
    forbidden = ("plugins.knowsys", "plugins.gnosis", "plugins.zetesis")

    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text(), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for fp in forbidden:
                        assert not alias.name.startswith(fp), (
                            f"{py}: forbidden import {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                mod_name = node.module or ""
                for fp in forbidden:
                    assert not mod_name.startswith(fp), (
                        f"{py}: forbidden import from {mod_name}"
                    )


def test_intention_root_never_leaks_kosmos_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default resolution paths must all live outside the repo tree.

    Colossus safety invariant: even with no env override, the scaffolder
    writes to XDG state or ~/.local/state — never inside the working tree.
    """
    monkeypatch.delenv(INTENTION_ROOT_ENV, raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)

    root = resolve_intention_root()
    repo_root = Path(__file__).resolve().parents[3]

    assert repo_root not in root.parents
    assert root != repo_root
