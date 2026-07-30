"""Contract tests for Praxis constitution loader (Stage 2.1, ADR-032).

Covers:

- Signing primitives (canonicalize / sign / verify / load_public_key /
  load_private_key)
- Verifier facade (default pubkey path + custom pubkey path + missing
  pubkey + malformed pubkey)
- ConstitutionLoader (existence check, YAML/JSON cross-check, signature
  verification, artifact accessor gating, deferred verification path)
- **Stage 2.1 DoD**: tampered constitution → boot refused
- Committed genesis triplet in ``governance/constitution/versions/v0001.*``
  verifies against the committed ``pubkey.pem``
- PraxisPlugin bootstrap: descriptor shape, panel registration,
  FrontendContractPort integration, tamper-refused-before-frontend-touch
"""

from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from plugins.praxis.constitution import (
    ConstitutionArtifact,
    ConstitutionError,
    ConstitutionLoader,
    ConstitutionMalformedError,
    ConstitutionNotFoundError,
    ConstitutionTamperError,
    ConstitutionVerifier,
)
from plugins.praxis.constitution.signing import (
    canonicalize,
    load_private_key,
    load_public_key,
    sign,
    verify,
)
from plugins.praxis.plugin import (
    PRAXIS_GOVERNANCE_PANEL_ID,
    PRAXIS_KERNEL_COMPAT,
    PRAXIS_PLUGIN_NAME,
    PRAXIS_STATE_NAMESPACE,
    PRAXIS_VERSION,
    PraxisPlugin,
    build_praxis_descriptor,
)
from ports.frontend_contract import (
    FrontendContractPort,
    KernelSchema,
    Panel,
    PanelSlot,
    PluginDescriptor,
    PluginRegistration,
    Route,
    UiParityStatus,
)


# ---------------------------------------------------------------------------
# Fixtures — a self-contained constitution artifact tree per test
# ---------------------------------------------------------------------------


@pytest.fixture
def keypair() -> tuple[Ed25519PrivateKey, bytes]:
    """Generate a fresh Ed25519 keypair. Returns (private, pubkey_pem_bytes)."""
    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


@pytest.fixture
def payload() -> dict[str, Any]:
    """A canonical minimal constitution payload."""
    return {
        "version_number": 1,
        "parent_version_number": None,
        "ratified_at": "2026-07-30T00:00:00Z",
        "ratified_by": "test",
        "title": "Test Constitution",
        "summary": "Fixture payload for contract tests.",
        "gutoe_axiom_refs": [],
        "policies": {},
        "cedar_policies": [],
    }


@pytest.fixture
def constitution_tree(
    tmp_path: Path,
    keypair: tuple[Ed25519PrivateKey, bytes],
    payload: dict[str, Any],
) -> Path:
    """Build a valid constitution artifact tree under ``tmp_path``.

    Layout::

        tmp_path/
          constitution/
            pubkey.pem
            versions/
              v0001.yaml
              v0001.json
              v0001.sig
    """
    priv, pub_pem = keypair
    root = tmp_path / "constitution"
    versions = root / "versions"
    versions.mkdir(parents=True)

    (root / "pubkey.pem").write_bytes(pub_pem)

    yaml_bytes = yaml.safe_dump(
        payload, sort_keys=False, allow_unicode=True
    ).encode("utf-8")
    (versions / "v0001.yaml").write_bytes(yaml_bytes)

    canonical = canonicalize(payload)
    (versions / "v0001.json").write_bytes(canonical)

    signature_b64 = sign(canonical, priv)
    (versions / "v0001.sig").write_text(signature_b64 + "\n", encoding="utf-8")

    return root


# ---------------------------------------------------------------------------
# Signing primitives
# ---------------------------------------------------------------------------


class TestSigning:
    """Tests for :mod:`plugins.praxis.constitution.signing`."""

    def test_canonicalize_returns_bytes(self, payload: dict[str, Any]) -> None:
        result = canonicalize(payload)
        assert isinstance(result, bytes)
        # Deterministic → same input, same output
        assert canonicalize(payload) == result

    def test_canonicalize_is_key_sort_stable(self) -> None:
        a = {"b": 1, "a": 2}
        b = {"a": 2, "b": 1}
        assert canonicalize(a) == canonicalize(b)

    def test_sign_verify_roundtrip(
        self,
        keypair: tuple[Ed25519PrivateKey, bytes],
        payload: dict[str, Any],
    ) -> None:
        priv, _ = keypair
        canonical = canonicalize(payload)
        sig_b64 = sign(canonical, priv)
        assert isinstance(sig_b64, str)
        assert verify(canonical, sig_b64, priv.public_key())

    def test_verify_rejects_tampered_payload(
        self,
        keypair: tuple[Ed25519PrivateKey, bytes],
        payload: dict[str, Any],
    ) -> None:
        priv, _ = keypair
        canonical = canonicalize(payload)
        sig_b64 = sign(canonical, priv)
        tampered = canonicalize({**payload, "title": "Malicious"})
        assert not verify(tampered, sig_b64, priv.public_key())

    def test_verify_rejects_malformed_base64(
        self,
        keypair: tuple[Ed25519PrivateKey, bytes],
        payload: dict[str, Any],
    ) -> None:
        _, _ = keypair
        canonical = canonicalize(payload)
        # Not valid base64url
        assert not verify(canonical, "!!!not-base64!!!", keypair[0].public_key())

    def test_verify_rejects_wrong_key(
        self,
        keypair: tuple[Ed25519PrivateKey, bytes],
        payload: dict[str, Any],
    ) -> None:
        priv, _ = keypair
        canonical = canonicalize(payload)
        sig_b64 = sign(canonical, priv)
        other_priv = Ed25519PrivateKey.generate()
        assert not verify(canonical, sig_b64, other_priv.public_key())

    def test_load_public_key_roundtrip(
        self, tmp_path: Path, keypair: tuple[Ed25519PrivateKey, bytes]
    ) -> None:
        _, pub_pem = keypair
        pem_path = tmp_path / "pubkey.pem"
        pem_path.write_bytes(pub_pem)
        loaded = load_public_key(pem_path)
        # Serializable back to the same PEM bytes
        assert (
            loaded.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            == pub_pem
        )

    def test_load_public_key_rejects_non_ed25519(
        self, tmp_path: Path
    ) -> None:
        # RSA pubkey PEM (obviously not Ed25519)
        from cryptography.hazmat.primitives.asymmetric import rsa

        rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        rsa_pem = rsa_priv.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        p = tmp_path / "rsa.pem"
        p.write_bytes(rsa_pem)
        with pytest.raises(TypeError):
            load_public_key(p)

    def test_load_private_key_roundtrip(
        self, tmp_path: Path, keypair: tuple[Ed25519PrivateKey, bytes]
    ) -> None:
        priv, _ = keypair
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        p = tmp_path / "privkey.pem"
        p.write_bytes(priv_pem)
        loaded = load_private_key(p)
        # Sign+verify with the loaded key
        canonical = canonicalize({"x": 1})
        sig_b64 = sign(canonical, loaded)
        assert verify(canonical, sig_b64, priv.public_key())


# ---------------------------------------------------------------------------
# ConstitutionVerifier facade
# ---------------------------------------------------------------------------


class TestConstitutionVerifier:
    def test_verifies_valid_signature(
        self,
        constitution_tree: Path,
        payload: dict[str, Any],
    ) -> None:
        verifier = ConstitutionVerifier(pubkey_path=constitution_tree / "pubkey.pem")
        canonical = (constitution_tree / "versions" / "v0001.json").read_bytes()
        sig_b64 = (constitution_tree / "versions" / "v0001.sig").read_text().strip()
        assert verifier.verify(canonical, sig_b64)

    def test_rejects_bad_signature(self, constitution_tree: Path) -> None:
        verifier = ConstitutionVerifier(pubkey_path=constitution_tree / "pubkey.pem")
        canonical = (constitution_tree / "versions" / "v0001.json").read_bytes()
        assert not verifier.verify(canonical, "AAAA")

    def test_missing_pubkey_raises_not_found(self, tmp_path: Path) -> None:
        verifier = ConstitutionVerifier(pubkey_path=tmp_path / "nope.pem")
        with pytest.raises(ConstitutionNotFoundError):
            verifier.verify(b"whatever", "AAAA")

    def test_malformed_pubkey_raises_malformed(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.pem"
        bad.write_bytes(b"-----BEGIN JUNK-----\nnope\n-----END JUNK-----\n")
        verifier = ConstitutionVerifier(pubkey_path=bad)
        with pytest.raises(ConstitutionMalformedError):
            verifier.verify(b"whatever", "AAAA")


# ---------------------------------------------------------------------------
# ConstitutionLoader — the boot-time orchestrator
# ---------------------------------------------------------------------------


class TestConstitutionLoader:
    def test_load_valid_triplet_returns_artifact(
        self, constitution_tree: Path
    ) -> None:
        loader = ConstitutionLoader(constitution_dir=constitution_tree)
        art = loader.artifact
        assert isinstance(art, ConstitutionArtifact)
        assert art.version_number == 1
        assert art.payload["title"] == "Test Constitution"

    def test_load_defer_then_call_load(self, constitution_tree: Path) -> None:
        loader = ConstitutionLoader(
            constitution_dir=constitution_tree, verify_on_init=False
        )
        # Accessing artifact before load raises
        with pytest.raises(ConstitutionNotFoundError):
            _ = loader.artifact
        art = loader.load()
        assert art.version_number == 1
        assert loader.artifact is art

    def test_missing_yaml_raises_not_found(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "versions" / "v0001.yaml").unlink()
        with pytest.raises(ConstitutionNotFoundError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_missing_json_raises_not_found(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "versions" / "v0001.json").unlink()
        with pytest.raises(ConstitutionNotFoundError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_missing_sig_raises_not_found(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "versions" / "v0001.sig").unlink()
        with pytest.raises(ConstitutionNotFoundError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_missing_pubkey_raises_not_found(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "pubkey.pem").unlink()
        with pytest.raises(ConstitutionNotFoundError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_bad_yaml_raises_malformed(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "versions" / "v0001.yaml").write_text(
            "not: valid: yaml: [oops"
        )
        with pytest.raises(ConstitutionMalformedError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_non_mapping_yaml_raises_malformed(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "versions" / "v0001.yaml").write_text(
            "- just\n- a\n- list\n"
        )
        with pytest.raises(ConstitutionMalformedError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_empty_signature_raises_malformed(
        self, constitution_tree: Path
    ) -> None:
        (constitution_tree / "versions" / "v0001.sig").write_text("   \n")
        with pytest.raises(ConstitutionMalformedError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_yaml_json_divergence_raises_tamper(
        self,
        constitution_tree: Path,
        payload: dict[str, Any],
    ) -> None:
        """YAML altered but JSON+sig left alone → tamper."""
        tampered = dict(payload)
        tampered["title"] = "MALICIOUS EDIT"
        (constitution_tree / "versions" / "v0001.yaml").write_bytes(
            yaml.safe_dump(tampered, sort_keys=False).encode("utf-8")
        )
        with pytest.raises(ConstitutionTamperError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_json_altered_raises_tamper(
        self, constitution_tree: Path
    ) -> None:
        """JSON altered but YAML+sig left alone → tamper."""
        # Prepend a byte so canonical equality check fails
        raw = (constitution_tree / "versions" / "v0001.json").read_bytes()
        (constitution_tree / "versions" / "v0001.json").write_bytes(b" " + raw)
        with pytest.raises(ConstitutionTamperError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_signature_altered_raises_tamper(
        self, constitution_tree: Path
    ) -> None:
        """Signature swapped for a valid-shape-but-wrong sig → tamper."""
        # Sign a different payload with a fresh key, base64url-encode
        other = Ed25519PrivateKey.generate()
        bogus_sig = base64.urlsafe_b64encode(
            other.sign(b"different content")
        ).decode()
        (constitution_tree / "versions" / "v0001.sig").write_text(
            bogus_sig + "\n"
        )
        with pytest.raises(ConstitutionTamperError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_wrong_pubkey_raises_tamper(
        self,
        constitution_tree: Path,
        keypair: tuple[Ed25519PrivateKey, bytes],
    ) -> None:
        """Pubkey replaced with an unrelated valid Ed25519 key → tamper."""
        other = Ed25519PrivateKey.generate()
        other_pem = other.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        (constitution_tree / "pubkey.pem").write_bytes(other_pem)
        with pytest.raises(ConstitutionTamperError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    def test_tamper_error_is_constitution_error(
        self, constitution_tree: Path
    ) -> None:
        """Callers can catch a single base class for any failure."""
        raw = (constitution_tree / "versions" / "v0001.json").read_bytes()
        (constitution_tree / "versions" / "v0001.json").write_bytes(b" " + raw)
        with pytest.raises(ConstitutionError):
            ConstitutionLoader(constitution_dir=constitution_tree)

    # ------------------------------------------------------------------
    # Stage 2.1 Definition of Done
    # ------------------------------------------------------------------

    def test_tampered_constitution_refuses_boot_build_sequence_2_1_dod(
        self,
        constitution_tree: Path,
        payload: dict[str, Any],
    ) -> None:
        """**Stage 2.1 DoD**: tampered constitution → boot refused.

        We simulate an attacker editing the YAML source of truth after
        ratification. The JSON+sig are untouched (attacker doesn't have
        the signing key). ``ConstitutionLoader.__init__`` MUST raise —
        that raise IS the boot-refusal signal.
        """
        attacker_edit = dict(payload)
        attacker_edit["policies"] = {"allow_all": True}
        attacker_edit["title"] = "Attacker Rewrite"
        (constitution_tree / "versions" / "v0001.yaml").write_bytes(
            yaml.safe_dump(attacker_edit, sort_keys=False).encode("utf-8")
        )

        with pytest.raises(ConstitutionTamperError):
            ConstitutionLoader(
                constitution_dir=constitution_tree, verify_on_init=True
            )


# ---------------------------------------------------------------------------
# Committed genesis triplet — regression: the on-disk genesis at
# governance/constitution/versions/v0001.* verifies against pubkey.pem
# ---------------------------------------------------------------------------


class TestCommittedGenesis:
    def test_committed_genesis_verifies(self) -> None:
        """The repo-committed genesis triplet must self-verify.

        Repos are cloned by future maintainers who expect the genesis to
        boot on a fresh checkout. This is a smoke test that the committed
        state is internally consistent.
        """
        repo_root = Path(__file__).resolve().parents[3]
        constitution_dir = repo_root / "governance" / "constitution"
        if not (constitution_dir / "versions" / "v0001.yaml").exists():
            pytest.skip("committed genesis not present on this checkout")

        loader = ConstitutionLoader(constitution_dir=constitution_dir)
        art = loader.artifact
        assert art.version_number == 1
        assert art.payload.get("ratified_by") == "genesis"
        assert art.payload.get("version_number") == 1


# ---------------------------------------------------------------------------
# PraxisPlugin bootstrap + FrontendContractPort registration
# ---------------------------------------------------------------------------


class _StubFrontendContract:
    """Test double implementing :class:`FrontendContractPort`.

    Stdlib-only, records every call in a public log for assertions.
    """

    def __init__(self) -> None:
        self.registered: dict[str, PluginDescriptor] = {}
        self.registration_log: list[str] = []
        self.unregistration_log: list[str] = []

    async def register_plugin(
        self, descriptor: PluginDescriptor
    ) -> PluginRegistration:
        self.registered[descriptor.name] = descriptor
        self.registration_log.append(descriptor.name)
        return PluginRegistration(
            descriptor=descriptor,
            registered_at=datetime.now(timezone.utc),
            ui_parity_status=UiParityStatus.IN_PROGRESS,
        )

    async def unregister_plugin(self, name: str) -> bool:
        if name in self.registered:
            del self.registered[name]
            self.unregistration_log.append(name)
            return True
        return False

    async def list_plugins(self) -> list[PluginDescriptor]:
        return list(self.registered.values())

    async def get_route_manifest(self) -> list[Route]:
        return [r for d in self.registered.values() for r in d.routes]

    async def get_design_tokens(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for d in self.registered.values():
            out.update(d.design_tokens)
        return out

    async def get_state_namespaces(self) -> list[str]:
        return [d.state_namespace for d in self.registered.values()]

    async def get_panel_manifest(
        self, slot: PanelSlot | None = None
    ) -> list[Panel]:
        panels: list[Panel] = []
        for d in self.registered.values():
            panels.extend(d.panels)
        if slot is not None:
            panels = [p for p in panels if p.slot == slot]
        return sorted(panels, key=lambda p: -p.priority)

    async def check_ui_parity(self, name: str) -> UiParityStatus:
        if name not in self.registered:
            return UiParityStatus.NOT_STARTED
        return UiParityStatus.IN_PROGRESS

    async def render_kernel_schema(self) -> KernelSchema:
        from ports.frontend_contract import KERNEL_SCHEMA_TITLE

        panels = tuple(p for d in self.registered.values() for p in d.panels)
        tokens: dict[str, str] = {}
        for d in self.registered.values():
            tokens.update(d.design_tokens)
        return KernelSchema(
            title=KERNEL_SCHEMA_TITLE,
            plugins=tuple(self.registered.values()),
            panels=panels,
            design_tokens=tokens,
            generated_at=datetime.now(timezone.utc),
        )

    def is_healthy(self) -> bool:
        return True

    async def close(self) -> None:
        pass


class TestPraxisDescriptor:
    def test_descriptor_shape(self) -> None:
        d = build_praxis_descriptor()
        assert d.name == PRAXIS_PLUGIN_NAME == "praxis"
        assert d.state_namespace == PRAXIS_STATE_NAMESPACE == "praxis"
        assert d.version == PRAXIS_VERSION
        assert d.kernel_compat == PRAXIS_KERNEL_COMPAT
        assert d.routes == ()
        assert d.design_tokens == {}
        # Stage 2.2 (ADR-033 Q1=C) added the APEX Approvals Queue panel.
        assert len(d.panels) == 2

    def test_descriptor_panel_slot_governance(self) -> None:
        d = build_praxis_descriptor()
        governance = [p for p in d.panels if p.slot == PanelSlot.GOVERNANCE]
        assert len(governance) == 1
        panel = governance[0]
        assert panel.id == PRAXIS_GOVERNANCE_PANEL_ID == "praxis.governance"
        assert panel.plugin_name == "praxis"
        assert panel.priority > 0
        assert panel.lazy_module

    def test_descriptor_stub_double_satisfies_port_protocol(self) -> None:
        """Sanity: the stub double is a valid FrontendContractPort."""
        stub = _StubFrontendContract()
        assert isinstance(stub, FrontendContractPort)


class TestPraxisPluginStart:
    async def test_start_verifies_constitution_and_registers(
        self, constitution_tree: Path
    ) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub,
            constitution_dir=constitution_tree,
        )
        assert not plugin.is_started
        await plugin.start()
        assert plugin.is_started
        assert plugin.constitution.version_number == 1
        assert stub.registration_log == ["praxis"]
        assert "praxis" in stub.registered
        assert plugin.registration.ui_parity_status == UiParityStatus.IN_PROGRESS

    async def test_start_is_idempotent(self, constitution_tree: Path) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )
        await plugin.start()
        await plugin.start()
        # Register called exactly once
        assert stub.registration_log == ["praxis"]

    async def test_stop_unregisters(self, constitution_tree: Path) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )
        await plugin.start()
        await plugin.stop()
        assert not plugin.is_started
        assert stub.unregistration_log == ["praxis"]
        assert "praxis" not in stub.registered

    async def test_stop_before_start_is_noop(
        self, constitution_tree: Path
    ) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )
        await plugin.stop()
        assert stub.unregistration_log == []

    async def test_tamper_refuses_boot_before_frontend_touch(
        self,
        constitution_tree: Path,
        payload: dict[str, Any],
    ) -> None:
        """Tamper must abort before any FrontendContractPort call.

        On tamper the plugin never exists from the kernel's perspective —
        no register_plugin call, no partially-registered state.
        """
        attacker = dict(payload)
        attacker["policies"] = {"allow_all": True}
        (constitution_tree / "versions" / "v0001.yaml").write_bytes(
            yaml.safe_dump(attacker, sort_keys=False).encode("utf-8")
        )
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )

        with pytest.raises(ConstitutionTamperError):
            await plugin.start()

        assert stub.registration_log == []
        assert not plugin.is_started

    async def test_accessors_raise_before_start(
        self, constitution_tree: Path
    ) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )
        with pytest.raises(RuntimeError):
            _ = plugin.constitution
        with pytest.raises(RuntimeError):
            _ = plugin.registration

    async def test_panel_appears_in_governance_slot(
        self, constitution_tree: Path
    ) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )
        await plugin.start()

        governance_panels = await stub.get_panel_manifest(
            slot=PanelSlot.GOVERNANCE
        )
        assert len(governance_panels) == 1
        assert governance_panels[0].plugin_name == "praxis"
        assert governance_panels[0].id == "praxis.governance"
        # Stage 2.2 (ADR-033) added a second panel in APPROVALS_QUEUE.
        approvals_panels = await stub.get_panel_manifest(
            slot=PanelSlot.APPROVALS_QUEUE
        )
        assert len(approvals_panels) == 1
        assert approvals_panels[0].plugin_name == "praxis"
        assert approvals_panels[0].id == "praxis.approvals"

    async def test_render_kernel_schema_includes_praxis(
        self, constitution_tree: Path
    ) -> None:
        stub = _StubFrontendContract()
        plugin = PraxisPlugin(
            frontend_contract=stub, constitution_dir=constitution_tree
        )
        await plugin.start()

        schema = await stub.render_kernel_schema()
        assert schema.title == "Kosmos"
        assert any(p.name == "praxis" for p in schema.plugins)
        assert any(pan.plugin_name == "praxis" for pan in schema.panels)
