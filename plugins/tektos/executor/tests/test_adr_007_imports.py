"""ADR-007 guard: the executor package must not import any other plugin.

Executor may import from:

* ``ports.*`` — formal port surface
* ``plugins.tektos.*`` — same plugin
* stdlib / third-party packages

Any ``from plugins.<other>`` or ``import plugins.<other>`` (where
``<other>`` is not ``tektos``) fails this test.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_EXECUTOR_PACKAGE = Path(__file__).resolve().parent.parent
_ALLOWED_PLUGIN = "tektos"


def _iter_executor_sources() -> list[Path]:
    return sorted(
        p
        for p in _EXECUTOR_PACKAGE.rglob("*.py")
        if "/tests/" not in str(p) and p.name != "__pycache__"
    )


def _bad_plugin_import(module_name: str) -> bool:
    """True iff ``module_name`` names a sibling plugin (not ``tektos``)."""

    if not module_name.startswith("plugins."):
        return False
    parts = module_name.split(".")
    # "plugins" alone is a bare namespace access; still forbidden.
    if len(parts) == 1:
        return True
    return parts[1] != _ALLOWED_PLUGIN


@pytest.mark.parametrize("source", _iter_executor_sources(), ids=lambda p: p.name)
def test_no_sibling_plugin_imports(source: Path) -> None:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _bad_plugin_import(alias.name):
                    offenders.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if _bad_plugin_import(mod):
                offenders.append(f"from {mod} import ...")
    assert not offenders, (
        f"{source.relative_to(_EXECUTOR_PACKAGE.parent.parent)} imports "
        f"sibling plugin(s) — ADR-007 violation: {offenders}"
    )
