"""Reference solution for tektos-plan-execution-smoke.

The verifier does not consume this file directly; it is retained per
Harbor task-format convention so a human can inspect the intended diff.
"""

from __future__ import annotations


def greet(name: str) -> str:
    return f"Hello, {name}!"


def main() -> str:
    return greet("Kosmos")
