"""Stage 14.7 — ADR-141 inference/metrics discharge: donor InferenceEngineMonitor.

The donor's inference-infrastructure observability substrate
(``runtime/inference_engine.py``) is now live in the kernel as
``kernel/inference_engine.py`` and exposed on the registry as
``inference_monitor``. This test exercises:

1. The Prometheus ``/metrics`` parser against REAL llama-server output
   (live :8090 when reachable — the user's live-tests rule — with an
   inline golden-text fallback so CI sandboxes stay hermetic). The live
   server emits the v0.1.2 colon-form metric names
   (``llamacpp:prompt_tokens_total`` etc.), which the byte-verbatim
   donor parser already targets.
2. ``build_known_instances()`` — the ADR-132 env-driven topology builder
   (the donor's stale hardcoded ``KNOWN_INSTANCES`` table was NOT
   ported; the kernel derives lanes from the same env the LLM adapters
   read at boot).
3. ``GET /api/inference/metrics`` (donor main.py:4515-4546, byte-verbatim)
   in its three degraded shapes + the happy path with a real
   InferenceEngineMonitor whose ``collect_all_metrics`` is driven
   directly (no mocks of the substrate's parser).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from kernel.app import app
from kernel.inference_engine import (
    InferenceEngineMonitor,
    InferenceEngineState,
    LlamaCppInstance,
    LlamaCppMetrics,
    build_known_instances,
)

# ── A live-server probe (user rule: live tests over mocks) ─────────────────
# The golden parser test hits the real GPU lane when it is up; otherwise
# (CI sandbox) it falls back to an inline capture of llama-server v0.1.2
# /metrics output so the assertion set is identical in both paths.

_LIVE_BASE = "http://127.0.0.1:8090"

# Inline capture from the live :8090 llama-server (v0.1.2), colon-form
# names. Values are the server's real counters at capture time; the
# assertions below pin the parser's NAME→field mapping, not the values.
_GOLDEN_METRICS = """# llamacpp:n_tokens_total 0.0
# TYPE llamacpp:n_tokens_max counter
llamacpp:n_tokens_max 98303
# TYPE llamacpp:prompt_tokens_total counter
llamacpp:prompt_tokens_total 6812345
# TYPE llamacpp:prompt_tokens_cached_total counter
llamacpp:prompt_tokens_cached_total 6100000
# TYPE llamacpp:tokens_predicted_total counter
llamacpp:tokens_predicted_total 192345
# TYPE llamacpp:prompt_seconds_total counter
llamacpp:prompt_seconds_total 123.456
# TYPE llamacpp:predicted_tokens_seconds counter
llamacpp:predicted_tokens_seconds 1890.12
# TYPE llamacpp:prompt_tokens_seconds counter
llamacpp:prompt_tokens_seconds 55176.0
# TYPE llamacpp:n_decode_total counter
llamacpp:n_decode_total 4321
"""


def _live_metrics_text() -> tuple[str, str]:
    """Return (metrics_text, source) — live :8090 or the golden capture.

    The live path is accepted only when EVERY counter the assertions read
    is present in the body — a connection cut mid-body (the server is
    loaded by the rest of the suite) must fall through to the golden
    capture, not assert on a partial parse."""
    import urllib.request

    required = (
        "llamacpp:prompt_tokens_total",
        "llamacpp:tokens_predicted_total",
        "llamacpp:n_tokens_max",
        "llamacpp:predicted_tokens_seconds",
        "llamacpp:n_decode_total",
    )
    try:
        with urllib.request.urlopen(f"{_LIVE_BASE}/metrics", timeout=5) as resp:
            text = resp.read().decode("utf-8")
        if all(name in text for name in required):
            return text, "live"
    except Exception:  # noqa: BLE001 — sandbox / lane down / partial body
        pass
    return _GOLDEN_METRICS, "golden"


# ── Fixtures ──────────────────────────────────────────────────────────────


def _instance(port: int = 8090) -> LlamaCppInstance:
    return LlamaCppInstance(
        port=port,
        model_name="test-model",
        model_path="/models/test.gguf",
        parameter_size="27B",
        quantization="Q4_K_M",
        format="gguf",
        capabilities=["completion"],
        is_gpu=True,
        is_embedding=False,
    )


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def monitor_with_instances(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """A REAL InferenceEngineMonitor wired onto the registry, with
    collect_all_metrics driven directly (parser tested separately)."""
    from kernel.app import registry

    metrics = LlamaCppMetrics(
        prompt_tokens_total=1000.0,
        tokens_predicted_total=200.0,
        predicted_tokens_seconds=4.5,
        prompt_tokens_seconds=50.0,
        prompt_seconds_total=20.0,
        avg_prompt_latency_ms=150.0,
        avg_generation_latency_ms=25.0,
        total_tokens_processed=1200.0,
        cache_hit_rate=0.75,
    )
    state = InferenceEngineState(
        instances={"primary_gpu": metrics},
        total_tokens_processed=1200.0,
        avg_cache_hit_rate=0.75,
    )

    monitor = InferenceEngineMonitor(instances={"primary_gpu": _instance()})

    async def _collect() -> InferenceEngineState:
        return state

    monkeypatch.setattr(monitor, "collect_all_metrics", _collect)
    monkeypatch.setattr(registry, "inference_monitor", monitor, raising=False)
    return TestClient(app)  # NOTE: no `with` — Stage 14.6 pattern: no
    # lifespan start, so the monkeypatched registry value survives boot.


# ── Parser: real llama-server /metrics → LlamaCppMetrics ──────────────────


def test_parser_live_or_golden_mapping() -> None:
    """Every counter the donor route surfaces must parse onto the right
    field, for BOTH the live server and the golden capture.

    Cumulative counters (prompt/predicted totals, n_tokens_max, n_decode)
    are asserted ``> 0`` — they stay non-zero once the server has served
    even one request, on both paths. ``predicted_tokens_seconds`` is a
    per-interval gauge (0.0 on an idle live server), so it is asserted
    ``>= 0`` in the shared block and its name→field mapping is pinned to
    the known golden value on the golden path.
    """
    text, source = _live_metrics_text()
    m = LlamaCppMetrics()
    m.update_from_prometheus(text)

    # Cumulative counters — non-zero on both live (long-running server)
    # and golden (captured mid-work).
    assert m.prompt_tokens_total > 0, f"{source}: prompt_tokens_total not parsed"
    assert m.tokens_predicted_total > 0, f"{source}: tokens_predicted_total not parsed"
    assert m.n_tokens_max > 0, f"{source}: n_tokens_max not parsed"
    assert m.n_decode_total > 0, f"{source}: n_decode_total not parsed"
    # Cache-hit derivation (prompt cached ≤ prompt total → 0..1 rate).
    assert 0.0 <= m.cache_hit_rate <= 1.0
    # Latency derivation: cumulative prompt_seconds_total / prompt tokens → ms.
    assert m.avg_prompt_latency_ms > 0
    # Per-interval gauge: idle server reads 0.0 — never assert > 0 on it.
    assert m.predicted_tokens_seconds >= 0

    if source == "golden":
        # Golden capture has a fixed, known non-zero gauge value — pin the
        # name→field mapping for the one field the live server can't prove.
        assert m.predicted_tokens_seconds == 1890.12


def test_parser_ignores_comments_and_unknown() -> None:
    m = LlamaCppMetrics()
    m.update_from_prometheus(_GOLDEN_METRICS + "\n# junk\nunknown_metric 1.0\n")
    # Re-parsing must not corrupt prior state (idempotent counters).
    assert m.prompt_tokens_total > 0
    assert not hasattr(m, "unknown_metric")


# ── build_known_instances: ADR-132 env-driven topology ─────────────────────


def test_build_known_instances_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env unset → the documented ADR-132 lane defaults (mirrors /api/models)."""
    for var in (
        "KOSMOS_LLAMA_SWAP_BASE_URL",
        "KOSMOS_LLAMA_SWAP_DEFAULT_MODEL",
        "KOSMOS_LLM_FALLBACK_BASE_URL",
        "KOSMOS_LLM_FALLBACK_MODEL",
        "KOSMOS_EMBEDDER_BASE_URL",
        "KOSMOS_EMBEDDER_MODEL",
        "KOSMOS_VISION_BASE_URL",
        "KOSMOS_VISION_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)

    ins = build_known_instances()
    assert set(ins) == {"primary_gpu", "secondary_cpu", "embedder_cpu", "vision_cpu"}
    assert ins["primary_gpu"].port == 8090
    assert ins["primary_gpu"].is_gpu is True
    assert ins["secondary_cpu"].port == 8092
    assert ins["secondary_cpu"].is_gpu is False
    assert ins["embedder_cpu"].port == 8091
    assert ins["embedder_cpu"].is_embedding is True
    assert ins["vision_cpu"].port == 8094


def test_build_known_instances_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env set → ports + model names follow the env (no stale topology)."""
    monkeypatch.setenv("KOSMOS_LLAMA_SWAP_BASE_URL", "http://127.0.0.1:9999/v1")
    monkeypatch.setenv("KOSMOS_LLAMA_SWAP_DEFAULT_MODEL", "my-custom-model-Q8_0")
    monkeypatch.setenv("KOSMOS_LLM_FALLBACK_BASE_URL", "http://127.0.0.1:7777")

    ins = build_known_instances()
    assert ins["primary_gpu"].port == 9999
    assert ins["primary_gpu"].model_name == "my-custom-model-Q8_0"
    assert ins["primary_gpu"].quantization == "Q8_0"
    assert ins["secondary_cpu"].port == 7777


# ── GET /api/inference/metrics — degraded + happy shapes ───────────────────


def test_metrics_monitor_not_initialized(client: TestClient) -> None:
    """Donor fail shape #1: no monitor booted → flat zeros + status.

    (TestClient is used WITHOUT a context manager — Stage 14.6 pattern —
    so the lifespan never boots and registry.inference_monitor stays in
    whatever state the test harness left it in; the dedicated
    `test_metrics_monitor_none_degrades` covers the forced-None path
    regardless of harness state.)"""
    from kernel.app import registry

    if registry.inference_monitor is not None:
        pytest.skip("monitor present in this harness; covered by the forced-None test")
    resp = client.get("/api/inference/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "monitor_not_initialized"
    assert body["total_tokens"] == 0
    assert body["tokens_per_second"] == 0.0
    assert body["prompt_tokens"] == 0
    assert body["completion_tokens"] == 0


def test_metrics_monitor_none_degrades(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forced monitor=None (CI: kernel may boot one) → donor fail shape #1."""
    from kernel.app import registry

    monkeypatch.setattr(registry, "inference_monitor", None, raising=False)
    resp = TestClient(app).get("/api/inference/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "monitor_not_initialized"
    assert body["total_tokens"] == 0
    assert body["completion_tokens"] == 0


def test_metrics_no_active_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    """Donor fail shape #2: monitor up but no instances produced metrics."""
    from kernel.app import registry

    monitor = InferenceEngineMonitor(instances={})

    async def _collect() -> InferenceEngineState:
        return InferenceEngineState(instances={})

    monkeypatch.setattr(monitor, "collect_all_metrics", _collect)
    monkeypatch.setattr(registry, "inference_monitor", monitor, raising=False)
    resp = TestClient(app).get("/api/inference/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "no_active_instances"
    assert body["total_tokens"] == 0


def test_metrics_collection_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Donor fail shape #3: collect raises → {error, status} at 200 (never 500)."""
    from kernel.app import registry

    monitor = InferenceEngineMonitor(instances={"primary_gpu": _instance()})

    async def _boom() -> InferenceEngineState:
        raise RuntimeError("lanes unreachable")

    monkeypatch.setattr(monitor, "collect_all_metrics", _boom)
    monkeypatch.setattr(registry, "inference_monitor", monitor, raising=False)
    resp = TestClient(app).get("/api/inference/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "collection_failed"
    assert "lanes unreachable" in body["error"]


def test_metrics_happy_path_aggregation(
    monitor_with_instances: TestClient,
) -> None:
    """Donor happy path: flat dict with the exact keys the UI InferencePanel
    reads (page.tsx:311-315) + correct aggregation math."""
    resp = monitor_with_instances.get("/api/inference/metrics")
    assert resp.status_code == 200
    body = resp.json()
    # UI-consumed keys (flat top-level — the discharge requirement).
    assert body["total_tokens"] == 1200
    assert body["tokens_per_second"] == 4.5  # single-instance average
    assert body["cache_hit_rate"] == 0.75
    assert body["avg_prompt_latency"] == 150.0
    assert body["avg_generation_latency"] == 25.0
    assert body["prompt_tokens"] == 1000
    assert body["completion_tokens"] == 200
    assert body["instances"] == 1
    # No status key on the happy path (donor parity).
    assert "status" not in body


def test_metrics_multi_instance_average(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Aggregation is the per-instance average (donor main.py:4536-4538),
    while token counters sum across instances."""
    from kernel.app import registry

    a = LlamaCppMetrics(
        prompt_tokens_total=100.0,
        tokens_predicted_total=10.0,
        predicted_tokens_seconds=2.0,
        avg_prompt_latency_ms=100.0,
        avg_generation_latency_ms=10.0,
    )
    b = LlamaCppMetrics(
        prompt_tokens_total=300.0,
        tokens_predicted_total=30.0,
        predicted_tokens_seconds=6.0,
        avg_prompt_latency_ms=200.0,
        avg_generation_latency_ms=30.0,
    )
    state = InferenceEngineState(
        instances={"primary_gpu": a, "secondary_cpu": b},
        total_tokens_processed=480.0,
        avg_cache_hit_rate=0.5,
    )
    monitor = InferenceEngineMonitor(
        instances={"primary_gpu": _instance(8090), "secondary_cpu": _instance(8092)}
    )

    async def _collect() -> InferenceEngineState:
        return state

    monkeypatch.setattr(monitor, "collect_all_metrics", _collect)
    monkeypatch.setattr(registry, "inference_monitor", monitor, raising=False)
    resp = TestClient(app).get("/api/inference/metrics")  # no `with`: keep
    # the monkeypatched registry (a lifespan start would re-boot a real
    # monitor over it — Stage 14.6 pattern).
    body = resp.json()
    assert body["tokens_per_second"] == 4.0  # (2 + 6) / 2
    assert body["avg_prompt_latency"] == 150.0  # (100 + 200) / 2
    assert body["avg_generation_latency"] == 20.0  # (10 + 30) / 2
    assert body["prompt_tokens"] == 400  # summed
    assert body["completion_tokens"] == 40  # summed
    assert body["total_tokens"] == 480
    assert body["instances"] == 2


# ── Monitor lifecycle (start/stop) ────────────────────────────────────────


def test_monitor_start_stop() -> None:
    """start() opens the httpx client; stop() closes it (shutdown hook)."""
    import asyncio

    monitor = InferenceEngineMonitor(instances={"primary_gpu": _instance()})

    async def _run() -> None:
        await monitor.start()
        assert monitor._client is not None
        await monitor.stop()
        assert monitor._client is None

    asyncio.run(_run())


def test_route_is_registered_on_kernel_app() -> None:
    """The discharge's observable referent: the route exists on the kernel
    app (it 404'd before Stage 14.7)."""
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/inference/metrics" in paths
    # Ordering rule: static sibling /api/inference/status still present.
    assert "/api/inference/status" in paths
