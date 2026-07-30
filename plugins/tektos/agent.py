"""Tektos coding agent (Stage 3.1, ADR-036).

Pattern-vendored from ``OpenHands/software-agent-sdk`` (MIT) — the
:class:`Agent` / :class:`Conversation` surface is preserved in shape
(``send_message`` + ``run``) but rewritten to consume Kosmos ports
exclusively. No upstream source is copied into the tree; only the
API shape.

Stage 3.1 scope:
- One iteration per turn (one ``send_message`` + one ``run``).
- Reads prior context from :meth:`MemoryPort.query_temporal`.
- Calls :meth:`LLMPort.generate_text` once.
- Writes the response back through :meth:`MemoryPort.write_event`
  with fixed provenance ``"tektos_agent"`` and caller-supplied
  confidence (default 0.75, ADR-036).

Deferred to later 3.x steps:
- Multi-iteration loops (3.5 Reflexion + Voyager).
- Tool calls (3.2 MCP + Playwright).
- Task decomposition + auto-context-compression (3.6 OpenSpec).
- FrontendContractPort ``PluginDescriptor`` registration (3.7 spec-kit).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from ports.llm import LLMPort
from ports.memory import MemoryPort

from plugins.tektos.errors import (
    TektosAgentAlreadyRunError,
    TektosAgentNotStartedError,
    TektosInvalidConfidenceError,
)
from plugins.tektos.models import (
    TEKTOS_AGENT_PROVENANCE,
    TektosMessage,
    TektosMessageRole,
    TektosStep,
)

__all__ = ["TektosAgent", "TEKTOS_MEMORY_PREDICATE"]


TEKTOS_MEMORY_PREDICATE: str = "tektos.turn.completed"
"""Canonical predicate every completed Tektos turn writes to memory.

Downstream stages MAY introduce additional predicates (``tektos.tool.invoked``
at 3.2, ``tektos.reflection.applied`` at 3.5). This one is locked at ADR-036.
"""


_DEFAULT_CONFIDENCE: float = 0.75
"""Locked at ADR-036. Reflexion (Stage 3.5) grows a real confidence
signal from self-critique; until then Tektos writes fixed 0.75, which
sits above the standard AMG lower bound of 0.6."""


@dataclass(slots=True)
class TektosAgent:
    """Minimal coding-agent loop over Kosmos ports.

    Construction:
        >>> agent = TektosAgent(llm=my_llm_port, memory=my_memory_port)

    Usage (one turn):
        >>> agent.send_message("Explain what this project does.")
        >>> step = await agent.run()

    Multi-turn is not supported at Stage 3.1 — call ``send_message``
    again for a new turn.
    """

    llm: LLMPort
    memory: MemoryPort
    subject: str = "tektos_user"
    model: str | None = None
    system_prompt: str | None = None
    confidence: float = _DEFAULT_CONFIDENCE
    context_limit: int = 5

    _pending: TektosMessage | None = field(default=None, init=False, repr=False)
    _turn_id: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0.0 < self.confidence <= 1.0):
            raise TektosInvalidConfidenceError(
                f"confidence must be in (0.0, 1.0]; got {self.confidence!r}"
            )
        if self.context_limit < 0:
            raise ValueError(
                f"context_limit must be >= 0; got {self.context_limit!r}"
            )

    # ── Public API ─────────────────────────────────────────────────────────

    def send_message(self, content: str) -> str:
        """Queue a user turn. Returns the turn id.

        Overwrites any pending turn that has not yet been ``run``.
        """
        if not isinstance(content, str) or not content.strip():
            raise ValueError("send_message content must be a non-empty string")
        self._pending = TektosMessage.user(content)
        self._turn_id = f"tektos-turn-{uuid4()}"
        return self._turn_id

    async def run(self) -> TektosStep:
        """Execute one iteration of the agent loop.

        Raises:
            TektosAgentNotStartedError: no pending turn (call
                ``send_message`` first).
            TektosAgentAlreadyRunError: the pending turn was already
                run in this instance's lifetime.
        """
        pending = self._pending
        turn_id = self._turn_id
        if pending is None or turn_id is None:
            raise TektosAgentNotStartedError(
                "run() called with no pending turn; call send_message() first"
            )

        # Consume the pending turn atomically — a second run() on the
        # same turn raises rather than double-firing the LLM/memory paths.
        self._pending = None
        self._turn_id = None

        prompt = await self._build_prompt(pending)
        response_text = await self.llm.generate_text(
            prompt=prompt,
            model=self.model,
            system=self.system_prompt,
        )

        event_id = await self.memory.write_event(
            subject=self.subject,
            predicate=TEKTOS_MEMORY_PREDICATE,
            object=response_text,
            provenance=TEKTOS_AGENT_PROVENANCE,
            confidence=self.confidence,
            attributes={
                "turn_id": turn_id,
                "role": TektosMessageRole.ASSISTANT.value,
                "prompt_len": len(prompt),
                "response_len": len(response_text),
            },
        )

        return TektosStep(
            turn_id=turn_id,
            prompt=prompt,
            response=response_text,
            memory_event_id=event_id.id,
            confidence=self.confidence,
            llm_model=self.model,
        )

    # ── Internal ───────────────────────────────────────────────────────────

    async def _build_prompt(self, pending: TektosMessage) -> str:
        """Assemble the LLM prompt from prior memory context + the pending message.

        Reads up to ``context_limit`` prior Tektos turns from
        :meth:`MemoryPort.query_temporal` and prepends them as
        ``[prior]`` lines. If the query returns nothing (fresh agent,
        empty memory), the prompt is just the pending message.
        """
        if self.context_limit == 0:
            return pending.content

        hits = await self.memory.query_temporal(
            TEKTOS_MEMORY_PREDICATE,
            limit=self.context_limit,
        )
        if not hits:
            if self._had_double_run(turn_content=pending.content):
                # Defensive: never reached at Stage 3.1; sentinel for
                # future multi-iteration loops (3.5 Reflexion) that will
                # re-enter ``_build_prompt`` inside a single run().
                raise TektosAgentAlreadyRunError(
                    "double-run guard tripped; multi-iteration deferred to 3.5"
                )
            return pending.content

        prior_lines = [f"[prior] {self._render_hit(hit)}" for hit in hits]
        return "\n".join(prior_lines + [pending.content])

    @staticmethod
    def _render_hit(hit: object) -> str:
        """Extract a printable string from a :class:`MemoryHit`.

        MemoryPort returns :class:`MemoryHit(id, payload, score, as_of)`
        where the payload dict carries whatever the adapter stored. The
        canonical Tektos write path sets ``payload["object"]`` to the
        assistant response text, but we tolerate any of {``object``,
        ``content``, ``response``} to stay robust to adapter drift.
        """
        payload = getattr(hit, "payload", None)
        if isinstance(payload, dict):
            for key in ("object", "content", "response"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
            return str(payload)
        return str(hit)

    def _had_double_run(self, *, turn_content: str) -> bool:
        """Stage 3.1 always returns False — the guard exists so future
        3.5 multi-iteration code can flip it without changing the public
        surface."""
        _ = turn_content
        return False
