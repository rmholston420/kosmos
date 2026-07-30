"""adapters.memory.dozerdb.dozerdb_graph_backend — Real Bolt GraphBackend (ADR-027, ADR-047).

Wraps `neo4j.AsyncGraphDatabase` (works against DozerDB 5.26.x which is
Neo4j-Bolt-compatible per PORTING_LEDGER). Satisfies the `GraphBackend`
Protocol declared in `adapters.memory.dozerdb.adapter`. All `neo4j` imports
are lazy so the fast unit tier does not require the driver on `PYTHONPATH`.

Key invariants (Kosmos custom instructions + ADR-023 rule 5):
- Label + relationship-type names are validated against an identifier regex
  before interpolation into a Cypher literal. This is the only place raw
  string interpolation is allowed; every other value crosses the boundary
  as a parameterized value.
- `is_healthy` is sync + non-throwing.
- `close` is async + idempotent + swallows driver errors into a warning log.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

log = logging.getLogger(__name__)

# Neo4j identifiers per the language spec:
#   https://neo4j.com/docs/cypher-manual/current/syntax/naming/
# We intentionally reject anything with characters that would need backtick
# quoting; the adapter contract does not require full Unicode identifier
# support and the tighter guard eliminates a large injection surface.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(kind: str, value: str) -> None:
    """Raise ValueError if `value` is not a safe Cypher identifier.

    `kind` is a short label (`label` / `rel_type`) used in the error message
    so callers see which parameter failed.
    """
    if not isinstance(value, str) or not _IDENT_RE.match(value):
        raise ValueError(
            f"DozerDbGraphBackend: invalid Cypher {kind} {value!r}; must match "
            f"{_IDENT_RE.pattern}. Reject-by-default guard for label injection."
        )


class DozerDbGraphBackend:
    """Bolt-backed `GraphBackend` for the DozerDbMemoryAdapter (ADR-027).

    Uses `neo4j.AsyncGraphDatabase.driver` as an async connection pool.
    A single driver is shared across all sessions; each `add_node` /
    `add_edge` / `query_cypher` opens a short-lived `AsyncSession`.

    Contract tests exercise this class with a mocked `neo4j` driver so no
    live DozerDB is required for the fast tier. The env-gated live tier
    (KOSMOS_STAGE_42_LIVE=1) exercises the real driver against the compose
    service in `ops/compose/memory.yml`.
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        *,
        database: str = "neo4j",
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver: Any | None = None
        self._closed = False
        self._init_error: str | None = None
        # Eagerly build the driver so a construction failure surfaces at
        # __init__ time rather than the first async call. The driver itself
        # is lazy about connecting so this is cheap and does not touch the
        # network.
        try:
            from neo4j import AsyncGraphDatabase  # lazy import

            self._driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:  # noqa: BLE001 — record + surface via is_healthy
            self._init_error = f"{type(e).__name__}: {e}"
            log.warning(
                "DozerDbGraphBackend init failed (uri=%s): %s",
                uri,
                self._init_error,
            )

    # ── async surface ───────────────────────────────────────────────────────

    async def add_node(self, label: str, props: dict[str, Any]) -> str:
        _validate_identifier("label", label)
        node_id = str(props.get("id") or uuid.uuid4())
        merged = {**props, "id": node_id}
        cypher = f"CREATE (n:{label} $props) RETURN n.id AS id"
        rows = await self._run(cypher, {"props": merged})
        if not rows:
            raise RuntimeError(
                f"DozerDbGraphBackend.add_node returned no rows for label={label!r}"
            )
        return str(rows[0]["id"])

    async def add_edge(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        props: dict[str, Any] | None,
    ) -> None:
        _validate_identifier("rel_type", rel_type)
        cypher = (
            "MATCH (s {id: $fid}), (t {id: $tid}) "
            f"CREATE (s)-[r:{rel_type} $props]->(t)"
        )
        await self._run(
            cypher,
            {"fid": from_id, "tid": to_id, "props": dict(props or {})},
        )

    async def query_cypher(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self._run(cypher, params or {})

    async def delete_node(self, node_id: str) -> None:
        await self._run(
            "MATCH (n {id: $nid}) DETACH DELETE n",
            {"nid": node_id},
        )

    # ── health / teardown ───────────────────────────────────────────────────

    def is_healthy(self) -> bool:
        """Sync + non-throwing readiness probe (ADR-023 rule 5)."""
        if self._closed:
            return False
        if self._init_error is not None:
            return False
        return self._driver is not None

    async def close(self) -> None:
        """Idempotent close — swallows driver errors into a warning."""
        if self._closed:
            return
        self._closed = True
        driver = self._driver
        self._driver = None
        if driver is None:
            return
        try:
            await driver.close()
        except Exception as e:  # noqa: BLE001
            log.warning(
                "DozerDbGraphBackend.close swallowed driver error: %s: %s",
                type(e).__name__,
                e,
            )

    # ── internal ────────────────────────────────────────────────────────────

    async def _run(
        self,
        cypher: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if self._closed or self._driver is None:
            raise RuntimeError(
                "DozerDbGraphBackend is closed or the driver failed to init; "
                f"init_error={self._init_error!r}"
            )
        async with self._driver.session(database=self._database) as session:
            result = await session.run(cypher, params)
            records = [dict(r) async for r in result]
            return records
