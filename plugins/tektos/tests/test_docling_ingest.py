"""Contract tests for the Tektos docling ingest subsystem.

Stage 3.10, ADR-044. Two tiers:

- Fast unit tier (always runs in ``make stage1-gate``): supplies a fake
  ``DoclingConverter`` shim so the tests never import ``docling``.
- Env-gated real-docling tier (Colossus only): activated by
  ``KOSMOS_STAGE_310_REAL_DOCLING=1`` and skipped otherwise.

The DoD literal anchor is
``test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod``.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from adapters.data.filesystem import (
    FilesystemDataAdapter,
    FilesystemStorage,
    NoOpSigner,
    SortedJsonCanonicalizer,
)
from plugins.tektos.ingest import (
    DOCLING_DEFAULT_PII_TIER,
    DOCLING_INGEST_PROVENANCE,
    DOCLING_INGEST_RECORD_TYPE,
    DOCLING_MAX_CONFIDENCE,
    DOCLING_MIN_CONFIDENCE,
    DOCLING_SUCCESS_CONFIDENCE,
    DOCLING_SUPPORTED_EXTENSIONS,
    DOCLING_UPSTREAM_COMMIT,
    DOCLING_UPSTREAM_LICENSE,
    DOCLING_UPSTREAM_PACKAGE,
    DOCLING_UPSTREAM_PYPI_VERSION,
    DOCLING_UPSTREAM_REPO,
    DoclingIngestFailure,
    UnsupportedExtensionError,
    confidence_for_ingest,
    ingest_document,
    normalize_extension,
    require_supported_extension,
)
from plugins.tektos.ingest.harness import (
    DoclingUnavailableError,
    resolve_default_converter_factory,
)
from plugins.tektos.ingest.models import DoclingIngestPayload, IngestedDocument
from ports.data import PIITier

FIXTURES = Path(__file__).parent / "fixtures" / "docling"
INGEST_PKG_DIR = Path(__file__).resolve().parents[1] / "ingest"


# ── Fake docling shim ───────────────────────────────────────────────────────


@dataclass
class _FakeDoc:
    body: dict[str, Any]

    def export_to_dict(self) -> dict[str, Any]:
        return dict(self.body)

    def export_to_markdown(self) -> str:
        return self.body.get("_markdown", "")


@dataclass
class _FakeResult:
    document: _FakeDoc


class _FakeConverter:
    """Deterministic docling stand-in used in the fast test tier.

    Records the last ``source`` seen so tests can assert the harness
    passed the resolved path through unchanged.
    """

    def __init__(self, body: dict[str, Any] | None = None) -> None:
        self.body = body or {
            "schema_name": "DoclingDocument",
            "version": "fake-1.0",
            "texts": [{"text": "hello kosmos"}],
            "_markdown": "# hello kosmos\n",
        }
        self.last_source: str | None = None

    def convert(self, source: str, /) -> _FakeResult:
        self.last_source = source
        return _FakeResult(document=_FakeDoc(body=dict(self.body)))


def _fresh_adapter(tmp_path: Path) -> FilesystemDataAdapter:
    return FilesystemDataAdapter(
        storage_root=tmp_path,
        canonicalizer=SortedJsonCanonicalizer(),
        signer=NoOpSigner(),
        storage=FilesystemStorage(tmp_path),
    )


# ── Locked policy constants ────────────────────────────────────────────────


def test_policy_locked_provenance() -> None:
    assert DOCLING_INGEST_PROVENANCE == "tektos-docling-ingest"


def test_policy_locked_record_type() -> None:
    assert DOCLING_INGEST_RECORD_TYPE == "tektos.ingest.document"


def test_policy_locked_upstream_identity() -> None:
    assert DOCLING_UPSTREAM_PACKAGE == "docling"
    assert DOCLING_UPSTREAM_PYPI_VERSION == "2.116.0"
    assert DOCLING_UPSTREAM_COMMIT == "ba8251e9cda84bab44cebe3b884119d3f50cb12a"
    assert DOCLING_UPSTREAM_LICENSE == "MIT"
    assert DOCLING_UPSTREAM_REPO == "https://github.com/docling-project/docling"


def test_policy_locked_confidence_bounds() -> None:
    assert DOCLING_MIN_CONFIDENCE == 0.0
    assert DOCLING_MAX_CONFIDENCE == 1.0
    assert DOCLING_SUCCESS_CONFIDENCE == DOCLING_MAX_CONFIDENCE


def test_policy_locked_default_pii_tier() -> None:
    assert DOCLING_DEFAULT_PII_TIER is PIITier.INTERNAL


def test_policy_locked_supported_extensions() -> None:
    assert DOCLING_SUPPORTED_EXTENSIONS == frozenset({".pdf", ".docx", ".html"})


def test_confidence_for_ingest_maps_success_to_max() -> None:
    assert confidence_for_ingest(True) == DOCLING_MAX_CONFIDENCE


def test_confidence_for_ingest_maps_failure_to_min() -> None:
    assert confidence_for_ingest(False) == DOCLING_MIN_CONFIDENCE


def test_confidence_for_ingest_rejects_non_bool() -> None:
    with pytest.raises(TypeError):
        confidence_for_ingest("yes")  # type: ignore[arg-type]


def test_normalize_extension_adds_dot_and_lowercases() -> None:
    assert normalize_extension("PDF") == ".pdf"
    assert normalize_extension(".Docx") == ".docx"
    assert normalize_extension("  HTML  ") == ".html"


def test_normalize_extension_rejects_non_str() -> None:
    with pytest.raises(TypeError):
        normalize_extension(123)  # type: ignore[arg-type]


def test_require_supported_extension_accepts_whitelist() -> None:
    for ext in (".pdf", ".docx", ".html", "PDF", ".Docx"):
        assert require_supported_extension(ext) in DOCLING_SUPPORTED_EXTENSIONS


def test_require_supported_extension_rejects_pptx() -> None:
    with pytest.raises(ValueError):
        require_supported_extension(".pptx")


# ── Model round-trips ──────────────────────────────────────────────────────


def test_docling_ingest_payload_to_payload_is_json_stable() -> None:
    payload = DoclingIngestPayload(
        source_filename="sample.html",
        source_extension=".html",
        source_size_bytes=42,
        docling_version="2.116.0",
        docling_commit=DOCLING_UPSTREAM_COMMIT,
        document={"schema_name": "DoclingDocument", "texts": []},
        markdown_export="",
    )
    d = payload.to_payload()
    # JSON round-trip must succeed with sort_keys — SortedJsonCanonicalizer
    # is what the FS adapter uses in these tests.
    reloaded = json.loads(json.dumps(d, sort_keys=True))
    assert reloaded == d


def test_ingested_document_to_attributes_omits_document_body() -> None:
    payload = DoclingIngestPayload(
        source_filename="sample.pdf",
        source_extension=".pdf",
        source_size_bytes=593,
        docling_version="2.116.0",
        docling_commit=DOCLING_UPSTREAM_COMMIT,
        document={"schema_name": "DoclingDocument"},
        markdown_export="",
    )
    doc = IngestedDocument(
        payload=payload,
        canonical_hash="deadbeef",
        storage_path="/tmp/x",
        exported_at_iso="2026-07-30T08:00:00+00:00",
    )
    attrs = doc.to_attributes()
    assert "document" not in attrs
    assert attrs["source_filename"] == "sample.pdf"
    assert attrs["source_extension"] == ".pdf"
    assert attrs["source_size_bytes"] == 593
    assert attrs["docling_version"] == "2.116.0"
    assert attrs["docling_commit"] == DOCLING_UPSTREAM_COMMIT


# ── Harness contract (fast tier, fake converter) ───────────────────────────


async def test_ingest_document_rejects_missing_file(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    try:
        with pytest.raises(FileNotFoundError):
            await ingest_document(
                tmp_path / "does-not-exist.pdf",
                data_port=adapter,
                converter_factory=lambda: _FakeConverter(),
            )
    finally:
        await adapter.close()


async def test_ingest_document_rejects_unsupported_extension(tmp_path: Path) -> None:
    src = tmp_path / "sample.pptx"
    src.write_bytes(b"not really pptx")
    adapter = _fresh_adapter(tmp_path)
    try:
        with pytest.raises(ValueError):
            await ingest_document(
                src,
                data_port=adapter,
                converter_factory=lambda: _FakeConverter(),
            )
    finally:
        await adapter.close()

    # UnsupportedExtensionError is a ValueError subclass — assert once.
    assert issubclass(UnsupportedExtensionError, ValueError)


async def test_ingest_document_rejects_directory(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    try:
        with pytest.raises(FileNotFoundError):
            await ingest_document(
                tmp_path,
                data_port=adapter,
                converter_factory=lambda: _FakeConverter(),
            )
    finally:
        await adapter.close()


async def test_ingest_document_writes_locked_envelope_shape(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    fake = _FakeConverter()
    try:
        result = await ingest_document(
            FIXTURES / "sample.html",
            data_port=adapter,
            converter_factory=lambda: fake,
        )
    finally:
        await adapter.close()

    # The harness passes the resolved path string to the converter.
    assert fake.last_source == str((FIXTURES / "sample.html").resolve())

    envelope_path = Path(result.storage_path)
    assert envelope_path.is_file()
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["record_type"] == DOCLING_INGEST_RECORD_TYPE
    assert envelope["provenance"] == DOCLING_INGEST_PROVENANCE
    assert envelope["confidence"] == DOCLING_SUCCESS_CONFIDENCE
    assert envelope["pii_tier"] == DOCLING_DEFAULT_PII_TIER.value
    payload = envelope["payload"]
    assert payload["source_filename"] == "sample.html"
    assert payload["source_extension"] == ".html"
    assert payload["docling_commit"] == DOCLING_UPSTREAM_COMMIT
    assert payload["document"]["schema_name"] == "DoclingDocument"
    assert isinstance(payload["markdown_export"], str)
    # Attributes are shallow filterable fields; the heavy `document`
    # JSON stays only in `payload`.
    attrs = envelope["attributes"]
    assert attrs["source_extension"] == ".html"
    assert "document" not in attrs


async def test_ingest_document_routes_restricted_to_restricted_prefix(
    tmp_path: Path,
) -> None:
    adapter = _fresh_adapter(tmp_path)
    try:
        result = await ingest_document(
            FIXTURES / "sample.html",
            data_port=adapter,
            converter_factory=lambda: _FakeConverter(),
            pii_tier=PIITier.RESTRICTED,
        )
    finally:
        await adapter.close()
    assert "/restricted/" in result.storage_path.replace("\\", "/")


async def test_ingest_document_raises_on_converter_exception(tmp_path: Path) -> None:
    class _BoomConverter:
        def convert(self, source: str, /) -> Any:
            raise RuntimeError("boom")

    adapter = _fresh_adapter(tmp_path)
    try:
        with pytest.raises(DoclingIngestFailure) as exc_info:
            await ingest_document(
                FIXTURES / "sample.html",
                data_port=adapter,
                converter_factory=lambda: _BoomConverter(),
            )
    finally:
        await adapter.close()
    assert "boom" in str(exc_info.value)


async def test_ingest_document_raises_on_missing_document_attr(tmp_path: Path) -> None:
    class _NoDocConverter:
        def convert(self, source: str, /) -> Any:
            return object()

    adapter = _fresh_adapter(tmp_path)
    try:
        with pytest.raises(DoclingIngestFailure):
            await ingest_document(
                FIXTURES / "sample.html",
                data_port=adapter,
                converter_factory=lambda: _NoDocConverter(),
            )
    finally:
        await adapter.close()


async def test_ingest_document_raises_on_non_str_markdown(tmp_path: Path) -> None:
    class _BadMarkdownDoc:
        def export_to_dict(self) -> dict[str, Any]:
            return {"schema_name": "DoclingDocument"}

        def export_to_markdown(self) -> Any:
            return b"bytes-not-str"

    class _BadMarkdownConverter:
        def convert(self, source: str, /) -> Any:
            @dataclass
            class R:
                document: Any

            return R(document=_BadMarkdownDoc())

    adapter = _fresh_adapter(tmp_path)
    try:
        with pytest.raises(DoclingIngestFailure):
            await ingest_document(
                FIXTURES / "sample.html",
                data_port=adapter,
                converter_factory=lambda: _BadMarkdownConverter(),
            )
    finally:
        await adapter.close()


async def test_ingest_document_merges_caller_attributes(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    try:
        result = await ingest_document(
            FIXTURES / "sample.html",
            data_port=adapter,
            converter_factory=lambda: _FakeConverter(),
            attributes={"upstream_ref": "unit-test", "source_extension": "overridden"},
        )
    finally:
        await adapter.close()
    envelope = json.loads(Path(result.storage_path).read_text(encoding="utf-8"))
    assert envelope["attributes"]["upstream_ref"] == "unit-test"
    # Caller keys win.
    assert envelope["attributes"]["source_extension"] == "overridden"


# ── DoD literal anchor ─────────────────────────────────────────────────────


async def test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod(
    tmp_path: Path,
) -> None:
    """Build-Sequence §3.10 DoD literal: 'PDF/DOCX/HTML → structured JSON-LD via DataPort.'

    Wires three committed fixtures (one each of .pdf, .docx, .html)
    through the fake docling shim and the real Stage-1.10 filesystem
    DataPort adapter, asserts three canonical envelopes appear under
    ``{tmp}/tektos.ingest.document/`` with correct record_type +
    provenance + pii_tier + shape-correct payload keys, and asserts
    ``check_format_health()`` reports zero degraded envelopes.
    """
    fixtures = [
        FIXTURES / "sample.pdf",
        FIXTURES / "sample.docx",
        FIXTURES / "sample.html",
    ]
    assert all(p.is_file() for p in fixtures)

    adapter = _fresh_adapter(tmp_path)
    handles: list[str] = []
    try:
        for source in fixtures:
            result = await ingest_document(
                source,
                data_port=adapter,
                converter_factory=lambda src=source: _FakeConverter(
                    body={
                        "schema_name": "DoclingDocument",
                        "version": "fake-1.0",
                        "_markdown": f"# from {src.name}\n",
                        "texts": [{"text": f"content from {src.name}"}],
                    }
                ),
            )
            handles.append(result.storage_path)

        envelopes_root = tmp_path / DOCLING_INGEST_RECORD_TYPE
        emitted = sorted(envelopes_root.glob("*.jsonld"))
        assert len(emitted) == 3

        seen_filenames: set[str] = set()
        for env_path in emitted:
            env = json.loads(env_path.read_text(encoding="utf-8"))
            assert env["record_type"] == DOCLING_INGEST_RECORD_TYPE
            assert env["provenance"] == DOCLING_INGEST_PROVENANCE
            assert env["confidence"] == DOCLING_SUCCESS_CONFIDENCE
            assert env["pii_tier"] == DOCLING_DEFAULT_PII_TIER.value
            assert env["@type"] == "CanonicalExport"
            # JSON-LD envelope contract from ADR-028.
            assert env["@context"].startswith("https://kosmos.local/context/")
            payload = env["payload"]
            for key in (
                "source_filename",
                "source_extension",
                "source_size_bytes",
                "docling_version",
                "docling_commit",
                "document",
                "markdown_export",
            ):
                assert key in payload
            assert payload["source_extension"] in DOCLING_SUPPORTED_EXTENSIONS
            seen_filenames.add(payload["source_filename"])

        assert seen_filenames == {"sample.pdf", "sample.docx", "sample.html"}

        health = await adapter.check_format_health()
        assert health.canonicalizer_ok
        assert health.storage_ok
        assert health.degraded_reasons == ()
    finally:
        await adapter.close()


# ── ADR-007 AST guard ──────────────────────────────────────────────────────


def test_docling_ingest_imports_no_other_plugins_adr_007() -> None:
    """ADR-007: no plugin may import another plugin's package directly.

    Statically walk every ``.py`` file under
    ``plugins/tektos/ingest/`` and reject any ``import plugins.<other>``
    that is not ``plugins.tektos`` itself.
    """
    offenders: list[tuple[str, str]] = []
    for py_path in INGEST_PKG_DIR.rglob("*.py"):
        source = py_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    if mod.startswith("plugins.") and not mod.startswith(
                        "plugins.tektos"
                    ):
                        offenders.append((str(py_path), mod))
                continue
            else:
                continue
            if mod.startswith("plugins.") and not mod.startswith("plugins.tektos"):
                offenders.append((str(py_path), mod))
    assert offenders == [], f"ADR-007 violation(s): {offenders}"


# ── Env-gated real docling tier ─────────────────────────────────────────────


def _real_docling_available() -> bool:
    return importlib.util.find_spec("docling") is not None


@pytest.mark.skipif(
    os.environ.get("KOSMOS_STAGE_310_REAL_DOCLING") != "1"
    or not _real_docling_available(),
    reason=(
        "Real docling tier is Colossus-only. Set "
        "KOSMOS_STAGE_310_REAL_DOCLING=1 and install `.[ingest]`."
    ),
)
async def test_real_docling_ingests_html_fixture_end_to_end(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    try:
        factory = resolve_default_converter_factory()
        # Factory must at least be callable and not raise import errors
        # here because the skipif above already gated on
        # ``docling`` being importable.
        assert callable(factory)
        try:
            result = await ingest_document(
                FIXTURES / "sample.html",
                data_port=adapter,
                converter_factory=factory,
            )
        except DoclingUnavailableError:
            pytest.skip("docling factory disagreed with importlib.util.find_spec")
    finally:
        await adapter.close()

    envelope = json.loads(Path(result.storage_path).read_text(encoding="utf-8"))
    assert envelope["record_type"] == DOCLING_INGEST_RECORD_TYPE
    assert envelope["provenance"] == DOCLING_INGEST_PROVENANCE
    assert envelope["pii_tier"] == DOCLING_DEFAULT_PII_TIER.value
    assert envelope["payload"]["source_filename"] == "sample.html"
    assert isinstance(envelope["payload"]["document"], dict)
    assert isinstance(envelope["payload"]["markdown_export"], str)
