"""Environment starting point for the tektos-plan-execution-smoke fixture.

The agent must rename ``greet_old`` to ``greet`` and update its own callers.
"""

from __future__ import annotations


def greet_old(name: str) -> str:
    return f"Hello, {name}!"


def main() -> str:
    return greet_old("Kosmos")
