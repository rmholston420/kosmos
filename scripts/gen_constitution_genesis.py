#!/usr/bin/env python3
"""Generate the Kosmos genesis constitution artifact triplet.

One-shot generator (idempotent per invocation, non-idempotent across
invocations because it mints a fresh Ed25519 keypair each time). Committed
to the repo for reproducibility per ADR-032.

Outputs (relative to monorepo root):

- ``governance/constitution/pubkey.pem`` — genesis Ed25519 public key
  (committed)
- ``governance/constitution/versions/v0001.yaml`` — human-authored
  genesis (committed)
- ``governance/constitution/versions/v0001.json`` — JCS canonicalization
  of v0001.yaml (committed)
- ``governance/constitution/versions/v0001.sig`` — Ed25519 detached
  signature over v0001.json, base64url ASCII (committed)
- ``.secrets/genesis/privkey.pem`` — genesis Ed25519 private key
  (NOT committed; .secrets/ is gitignored)

The private key is retained locally only. Amendment workflow (Synedrion,
Phase 6.3) will define proper key rotation. Until then, regenerating the
genesis simply reissues the whole triplet with a fresh keypair.

Usage::

    python scripts/gen_constitution_genesis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

# Repo-local sys.path so plugins.praxis.constitution.signing imports work
# whether the script runs before an editable install or after.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.praxis.constitution.signing import (  # noqa: E402
    canonicalize,
    sign,
)

import yaml  # noqa: E402


GENESIS_PAYLOAD = {
    "version_number": 1,
    "parent_version_number": None,
    "ratified_at": "2026-07-30T00:00:00Z",
    "ratified_by": "genesis",
    "title": "Kosmos Constitution Genesis",
    "summary": (
        "Initial genesis constitution artifact. Ratified at Kosmos Stage 2.1 "
        "as the boot-time integrity anchor. Amendment workflow deferred to "
        "Synedrion (Phase 6.3, ADR-032)."
    ),
    "gutoe_axiom_refs": [],
    "policies": {},
    "cedar_policies": [],
}


def main() -> int:
    """Generate and write genesis artifacts. Return process exit code."""
    constitution_dir = _REPO_ROOT / "governance" / "constitution"
    versions_dir = constitution_dir / "versions"
    secrets_dir = _REPO_ROOT / ".secrets" / "genesis"

    constitution_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)
    secrets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fresh Ed25519 keypair
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    # 2. Public key → committed PEM
    pubkey_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    (constitution_dir / "pubkey.pem").write_bytes(pubkey_pem)

    # 3. Private key → gitignored PEM
    privkey_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    (secrets_dir / "privkey.pem").write_bytes(privkey_pem)

    # 4. YAML source of truth
    yaml_bytes = yaml.safe_dump(
        GENESIS_PAYLOAD, sort_keys=False, allow_unicode=True
    ).encode("utf-8")
    (versions_dir / "v0001.yaml").write_bytes(yaml_bytes)

    # 5. JCS canonical JSON (what gets signed)
    canonical = canonicalize(GENESIS_PAYLOAD)
    (versions_dir / "v0001.json").write_bytes(canonical)

    # 6. Detached Ed25519 signature over canonical JSON
    signature_b64 = sign(canonical, priv)
    (versions_dir / "v0001.sig").write_text(signature_b64 + "\n", encoding="utf-8")

    print(f"Wrote pubkey → {constitution_dir / 'pubkey.pem'}")
    print(f"Wrote privkey → {secrets_dir / 'privkey.pem'} (gitignored)")
    print(f"Wrote yaml → {versions_dir / 'v0001.yaml'}")
    print(f"Wrote json → {versions_dir / 'v0001.json'}")
    print(f"Wrote sig  → {versions_dir / 'v0001.sig'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
