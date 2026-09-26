"""Stage 14.9 — ADR-141 `/ws/pty` discharge: PTY WebSocket route tests.

The route (``kernel/app.py``) is a byte-verbatim port of the donor
(``tektos-ultima`` ``main.py:5830-5936``) with two documented fixes:

1. The donor's ``os.set_blocking(fd, False)`` was a latent bug — the
   blocking ``os.read`` in the executor is the correct pattern, and a
   non-blocking fd made the first read raise ``BlockingIOError``,
   silently killing the pump before any shell output arrived. Dropped.
2. The receive loop now races incoming client frames against pump
   completion so the ``"exit"`` frame is actually sent when the shell
   exits (the donor's loop would wait forever for client input after
   the pump hit EOF).

These tests drive a *real* forked login shell over a real PTY through
Starlette's ``TestClient`` websocket transport — no fake websocket, no
fake PTY. GPU-free, no daemon, no network.
"""

from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient

from kernel.app import app

# A token unique to this test file so shell output can never fake a match.
ECHO_TOKEN = "KOSMOS_PTY_STAGE149"


def _ws(path: str = "/ws/pty"):
    """Context manager for a live TestClient websocket — matches the
    established kernel pattern (test_stage_6_5_4_websocket_event_bus_bridge):
    plain TestClient + `with client.websocket_connect(...) as ws:`.
    (The kernel TestClient no-`with` rule applies to HTTP requests.)
    """
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        client = TestClient(app)
        with client.websocket_connect(path) as ws:
            yield ws

    return _cm()


def _receive_until(ws, predicate, max_frames: int = 400, frame_note: str = ""):
    """Read frames until ``predicate(frame)`` is true.

    Returns the matching frame (dict) or None after ``max_frames``.
    """
    for _ in range(max_frames):
        raw = ws.receive_text()
        try:
            frame = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue
        if predicate(frame):
            return frame
    raise AssertionError(
        f"no frame matching {frame_note!r} within {max_frames} frames"
    )


def _drain_until_prompt(ws, max_frames: int = 400) -> None:
    """Consume frames until the login shell has printed a prompt."""
    _receive_until(
        ws,
        lambda f: f.get("type") == "output"
        and ("$" in f.get("data", "") or "%" in f.get("data", "")),
        max_frames=max_frames,
        frame_note="prompt",
    )


def test_ws_pty_route_registered() -> None:
    paths = [
        getattr(r, "path", None) for r in app.routes
    ]
    assert "/ws/pty" in paths, f"/ws/pty missing from {sorted(p for p in paths if p)}"
    # Static-path ordering rule sanity: it must not shadow any /ws/*param*
    # sibling (no other /ws/ routes exist in the kernel today).
    ws_paths = [p for p in paths if p and p.startswith("/ws/")]
    assert ws_paths == ["/ws/pty"], f"unexpected /ws/* routes: {ws_paths}"


def test_ws_pty_login_shell_prompt_arrives() -> None:
    with _ws() as ws:
        _drain_until_prompt(ws)


def test_ws_pty_input_echo_roundtrip() -> None:
    with _ws() as ws:
        _drain_until_prompt(ws)
        ws.send_text(json.dumps({"type": "input", "data": f"echo {ECHO_TOKEN}\r"}))
        frame = _receive_until(
            ws,
            lambda f: f.get("type") == "output" and ECHO_TOKEN in f.get("data", ""),
            frame_note="echoed token",
        )
        assert frame["type"] == "output"
        assert ECHO_TOKEN in frame["data"]


def test_ws_pty_resize_keeps_session_alive() -> None:
    with _ws() as ws:
        _drain_until_prompt(ws)
        ws.send_text(json.dumps({"type": "resize", "rows": 40, "cols": 120}))
        # Session must remain functional after a resize.
        ws.send_text(json.dumps({"type": "input", "data": f"echo {ECHO_TOKEN}-RESIZED\r"}))
        frame = _receive_until(
            ws,
            lambda f: f.get("type") == "output" and f"{ECHO_TOKEN}-RESIZED" in f.get("data", ""),
            frame_note="post-resize echo",
        )
        assert frame["type"] == "output"


def test_ws_pty_exit_frame_on_shell_exit() -> None:
    """The Stage-14.9 receive/pump race: when the shell exits, the server
    must send {"type": "exit", "code": N} instead of hanging on receive."""
    with _ws() as ws:
        _drain_until_prompt(ws)
        ws.send_text(json.dumps({"type": "input", "data": "exit\r"}))
        start = time.monotonic()
        frame = _receive_until(
            ws,
            lambda f: f.get("type") == "exit",
            max_frames=200,
            frame_note="exit frame",
        )
        elapsed = time.monotonic() - start
        # The pump hits EOF almost immediately after the shell exits; the
        # exit frame must arrive fast (not after a client-side timeout).
        assert elapsed < 15.0, f"exit frame took {elapsed:.1f}s (server hang?)"
        assert frame["type"] == "exit"
        assert isinstance(frame.get("code"), int)


def test_ws_pty_malformed_json_is_ignored() -> None:
    """Garbage frames are skipped (donor behavior), session survives."""
    with _ws() as ws:
        _drain_until_prompt(ws)
        ws.send_text("this is not json")
        ws.send_text(json.dumps({"type": "unknown", "data": "x"}))
        # Session must still respond.
        ws.send_text(json.dumps({"type": "input", "data": f"echo {ECHO_TOKEN}-MALF\r"}))
        frame = _receive_until(
            ws,
            lambda f: f.get("type") == "output" and f"{ECHO_TOKEN}-MALF" in f.get("data", ""),
            frame_note="post-malformed echo",
        )
        assert frame["type"] == "output"


def test_ws_pty_endpoint_signature() -> None:
    """The endpoint is an async coroutine function taking one websocket arg."""
    import inspect

    fn = None
    for r in app.routes:
        if getattr(r, "path", None) == "/ws/pty":
            fn = getattr(r, "endpoint", None)
            break
    assert fn is not None
    assert inspect.iscoroutinefunction(fn)
    params = list(inspect.signature(fn).parameters)
    assert len(params) == 1
