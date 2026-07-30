"""Boot-time constitution loader — Stage 2.1 DoD entry point.

Reads the ratified constitution artifact triplet from disk
(``vNNNN.yaml`` / ``vNNNN.json`` / ``vNNNN.sig``), enforces three
invariants, and either exposes the loaded payload or raises a
:class:`ConstitutionError` subclass. A raised error at construction time
IS the Stage 2.1 DoD's "boot refused" signal.

Invariants enforced (in order):

1. **Artifacts exist.** All three files (yaml, json, sig) must be present.
   Missing → :class:`ConstitutionNotFoundError`.
2. **YAML parses and matches JSON.** The JSON copy must equal the JCS
   canonicalization of the parsed YAML. Divergence → this is tamper: the
   YAML and JSON diverge, so we cannot trust either. →
   :class:`ConstitutionTamperError`.
3. **Signature verifies.** The Ed25519 signature must verify against the
   configured public key over the JCS canonical JSON bytes. →
   :class:`ConstitutionTamperError` on failure.

The DoD test tampers with the YAML/JSON and asserts that
:meth:`ConstitutionLoader.__init__` raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from plugins.praxis.constitution.errors import (
    ConstitutionMalformedError,
    ConstitutionNotFoundError,
    ConstitutionTamperError,
)
from plugins.praxis.constitution.signing import canonicalize
from plugins.praxis.constitution.verifier import ConstitutionVerifier


_DEFAULT_CONSTITUTION_DIR = (
    Path(__file__).resolve().parents[3] / "governance" / "constitution"
)


@dataclass(frozen=True, slots=True)
class ConstitutionArtifact:
    """A verified constitution version, produced by :class:`ConstitutionLoader`.

    Frozen dataclass — the loaded payload is immutable once verification
    passes. Any downstream mutation would invalidate the "signature-checked
    at boot" guarantee.

    Attributes:
        version_number: Integer version (matches the ``vNNNN`` filename
            prefix).
        yaml_text: Raw YAML source as read from disk (UTF-8 text).
        json_text: Raw canonical JSON as read from disk (UTF-8 text). This
            is what the signature was computed over.
        signature_b64: Detached Ed25519 signature, base64url-encoded ASCII.
        payload: Parsed YAML payload as a Python dict. Equivalent to
            ``json.loads(json_text)`` after normalization; carries the
            constitution fields (``title``, ``policies``, etc.).
    """

    version_number: int
    yaml_text: str
    json_text: str
    signature_b64: str
    payload: dict[str, Any]


class ConstitutionLoader:
    """Boot-time constitution loader — refuses boot on tamper.

    Construction runs all three invariants immediately by default. To
    defer verification (e.g. for tooling that only wants to inspect
    artifacts), pass ``verify_on_init=False`` and call :meth:`load`
    explicitly.

    Args:
        constitution_dir: Directory containing ``versions/vNNNN.*`` and
            (implicitly) the pubkey referenced by ``verifier``. Defaults
            to ``governance/constitution/`` at the monorepo root.
        version_number: Which version to load. Stage 2.1 only supports
            ``1`` (the genesis triplet).
        verifier: Optional custom :class:`ConstitutionVerifier`. If
            omitted, defaults to a verifier bound to
            ``constitution_dir/pubkey.pem``.
        verify_on_init: If ``True`` (default), load and verify in
            ``__init__``. A tamper failure raises immediately — this is
            the Stage 2.1 DoD signal.
    """

    def __init__(
        self,
        constitution_dir: Path | None = None,
        version_number: int = 1,
        verifier: ConstitutionVerifier | None = None,
        verify_on_init: bool = True,
    ) -> None:
        self.constitution_dir = constitution_dir or _DEFAULT_CONSTITUTION_DIR
        self.versions_dir = self.constitution_dir / "versions"
        self.version_number = version_number
        self._verifier = verifier or ConstitutionVerifier(
            pubkey_path=self.constitution_dir / "pubkey.pem"
        )
        self._artifact: ConstitutionArtifact | None = None

        if verify_on_init:
            self._artifact = self.load()

    @property
    def artifact(self) -> ConstitutionArtifact:
        """Return the verified constitution artifact.

        Raises:
            ConstitutionError: If :meth:`load` has not yet run
                successfully.
        """
        if self._artifact is None:
            raise ConstitutionNotFoundError(
                "Constitution has not been loaded yet — call load() or "
                "construct with verify_on_init=True"
            )
        return self._artifact

    def load(self) -> ConstitutionArtifact:
        """Load, cross-check, and cryptographically verify the triplet.

        Returns:
            The verified :class:`ConstitutionArtifact`.

        Raises:
            ConstitutionNotFoundError: A required artifact is missing.
            ConstitutionMalformedError: An artifact is present but
                unparseable (bad YAML, bad JSON, bad base64).
            ConstitutionTamperError: The signature fails to verify, or the
                on-disk JSON does not match the JCS canonicalization of
                the on-disk YAML.
        """
        stem = f"v{self.version_number:04d}"
        yaml_path = self.versions_dir / f"{stem}.yaml"
        json_path = self.versions_dir / f"{stem}.json"
        sig_path = self.versions_dir / f"{stem}.sig"

        # 1. Existence
        for path in (yaml_path, json_path, sig_path):
            if not path.exists():
                raise ConstitutionNotFoundError(
                    f"Constitution artifact missing: {path}"
                )

        # 2. Parse
        try:
            yaml_text = yaml_path.read_text(encoding="utf-8")
            payload = yaml.safe_load(yaml_text)
        except (OSError, yaml.YAMLError) as exc:
            raise ConstitutionMalformedError(
                f"Cannot parse {yaml_path}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ConstitutionMalformedError(
                f"Constitution YAML at {yaml_path} did not parse to a "
                f"mapping — got {type(payload).__name__}"
            )

        try:
            json_text = json_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConstitutionMalformedError(
                f"Cannot read {json_path}: {exc}"
            ) from exc

        try:
            signature_b64 = sig_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ConstitutionMalformedError(
                f"Cannot read {sig_path}: {exc}"
            ) from exc
        if not signature_b64:
            raise ConstitutionMalformedError(
                f"Constitution signature at {sig_path} is empty"
            )

        # 3. YAML/JSON cross-check — the on-disk JSON must be the JCS
        # canonicalization of the on-disk YAML. If they diverge, we cannot
        # trust either artifact.
        expected_json_bytes = canonicalize(payload)
        actual_json_bytes = json_text.encode("utf-8")
        if expected_json_bytes != actual_json_bytes:
            raise ConstitutionTamperError(
                f"Constitution YAML/JSON divergence at v{self.version_number:04d}: "
                f"on-disk JSON is not the JCS canonicalization of on-disk YAML"
            )

        # 4. Signature verification
        try:
            ok = self._verifier.verify(actual_json_bytes, signature_b64)
        except (
            ConstitutionNotFoundError,
            ConstitutionMalformedError,
        ):
            # Propagate pubkey-related errors as-is; they are not
            # tamper of the constitution itself.
            raise
        if not ok:
            raise ConstitutionTamperError(
                f"Constitution signature verification failed for "
                f"v{self.version_number:04d}"
            )

        artifact = ConstitutionArtifact(
            version_number=self.version_number,
            yaml_text=yaml_text,
            json_text=json_text,
            signature_b64=signature_b64,
            payload=payload,
        )
        self._artifact = artifact
        return artifact
