"""Kosmos repo-root conftest.

Ensures the monorepo root is on ``sys.path`` so tests can import top-level
packages that are not declared in ``[tool.setuptools].packages`` — notably
``ops`` (benchmarks + governance harnesses), ``kernel``, and ``scripts``.

Rationale:
    ``pip install -e .`` only installs the packages enumerated in
    pyproject.toml. Non-enumerated packages like ``ops`` remain importable
    only when the interpreter's ``sys.path[0]`` contains the repo root.
    Pytest's default rootdir handling covers that on some layouts but is
    fragile across Python versions, entry points (``pytest`` vs.
    ``python -m pytest``), and editable-install flavors. A repo-root
    conftest is the deterministic fix documented in the pytest docs:

        https://docs.pytest.org/en/stable/explanation/goodpractices.html
        #tests-outside-application-code

    The prepend is idempotent — repeated pytest invocations do not stack
    duplicates.

This file must remain minimal. It is imported extremely early in the
pytest bootstrap; anything that fails here fails the entire test run.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_REPO_ROOT_STR = str(_REPO_ROOT)

if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
