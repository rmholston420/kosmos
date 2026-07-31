"""ZetesisObservabilityStub — Protocol-conformant ObservabilityPort stub (ADR-056 sub-slice 2).

`trace` returns a no-op context-manager Span so `with obs.trace(...): ...`
compiles and runs. Metric methods are no-ops. Sub-slice 3+ replaces
with a real observability adapter.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any


class _NoOpSpan:
    """No-op Span. Conforms to ports.observability.Span Protocol."""

    def set_attribute(self, key: str, value: Any) -> None:
        return None

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        return None

    def record_exception(self, exc: BaseException) -> None:
        return None

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        # Do not swallow exceptions.
        return None


class ZetesisObservabilityStub:
    """Minimal ObservabilityPort stub. All methods are no-ops."""

    def trace(self, name: str, *, attributes: dict[str, Any] | None = None) -> _NoOpSpan:
        return _NoOpSpan()

    def score(
        self,
        name: str,
        value: float,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        return None

    def log_cost(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        usd: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        return None

    def bind_context(self, **keys: Any) -> None:
        return None

    def clear_context(self) -> None:
        return None

    def get_tracer(self, name: str) -> Any:
        return None

    def get_meter(self, name: str) -> Any:
        return None

    def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
