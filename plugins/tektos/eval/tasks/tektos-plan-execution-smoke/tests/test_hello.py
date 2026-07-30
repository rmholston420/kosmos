"""Verifier for tektos-plan-execution-smoke.

The Pier verifier runs this file with ``pytest`` inside the trial
sandbox. Exit code 0 -> PASS, non-zero -> FAIL.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_hello():
    src_dir = Path("/workspace/src")
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    if "hello" in sys.modules:
        del sys.modules["hello"]
    return importlib.import_module("hello")


def test_greet_returns_expected_string() -> None:
    hello = _load_hello()
    assert hasattr(hello, "greet"), "expected renamed function 'greet'"
    assert hello.greet("Kosmos") == "Hello, Kosmos!"


def test_greet_old_is_removed() -> None:
    hello = _load_hello()
    assert not hasattr(
        hello, "greet_old"
    ), "expected 'greet_old' to have been renamed to 'greet'"


def test_main_invokes_greet() -> None:
    hello = _load_hello()
    assert hello.main() == "Hello, Kosmos!"
