#!/usr/bin/env python3
"""Rebuild Kosmos v25 zip bundle for project-files sharing."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "projects" / "kosmos-4i2HipsQQjK4JixpXe0ODA" / "files"
ZIP_OUT = OUT_DIR / "Kosmos-v25-Bundle.zip"


# Files to include, mapped to their archive path.
INCLUDE_ROOT = [
    "BUILD_LOG.md",
    "DEBUG_LOG.md",
    "KNOWN_ISSUES.md",
    "SESSION_HANDOFF.md",
]
INCLUDE_DOCS = [
    "docs/Kosmos-Build-Spec-v25.md",
    "docs/Kosmos-Build-Sequence-v25.md",
    "docs/PORTING_LEDGER.md",
    "docs/PORT_CONTRACTS.md",
    "docs/Kosmos-ADRs-Bundle.md",  # place at ARCHIVE root, matching previous layout
]


def main() -> None:
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in INCLUDE_ROOT:
            src = ROOT / rel
            if src.exists():
                zf.write(src, arcname=rel)
        # ADRs bundle at archive root (matches previous v25 zip layout)
        adrs_bundle = ROOT / "docs" / "Kosmos-ADRs-Bundle.md"
        if adrs_bundle.exists():
            zf.write(adrs_bundle, arcname="Kosmos-ADRs-Bundle.md")
        # docs/ files
        for rel in INCLUDE_DOCS:
            if rel.endswith("Kosmos-ADRs-Bundle.md"):
                continue  # already added at root
            src = ROOT / rel
            if src.exists():
                zf.write(src, arcname=rel)
        # docs/adrs/*.md
        adr_dir = ROOT / "docs" / "adrs"
        for p in sorted(adr_dir.glob("ADR-*.md")):
            zf.write(p, arcname=f"docs/adrs/{p.name}")
    print(f"wrote {ZIP_OUT} ({ZIP_OUT.stat().st_size} bytes)")

    # Also update the docs/Kosmos-ADRs-Bundle.md copy in the project files repo
    shutil.copyfile(ROOT / "docs" / "Kosmos-ADRs-Bundle.md", OUT_DIR / "Kosmos-ADRs-Bundle.md")
    print(f"copied Kosmos-ADRs-Bundle.md to {OUT_DIR}")


if __name__ == "__main__":
    main()
