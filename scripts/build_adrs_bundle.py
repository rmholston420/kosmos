#!/usr/bin/env python3
"""Rebuild docs/Kosmos-ADRs-Bundle.md by concatenating adrs/README.md + every ADR-*.md in order."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "docs" / "adrs"
OUT = ROOT / "docs" / "Kosmos-ADRs-Bundle.md"


def adr_sort_key(p: Path) -> tuple[int, str]:
    m = re.match(r"ADR-(\d+)", p.stem)
    return (int(m.group(1)) if m else 999, p.name)


def main() -> None:
    files = sorted(
        [p for p in ADR_DIR.glob("ADR-*.md")],
        key=adr_sort_key,
    )
    total_adrs = len(files)
    open_adrs = []
    for p in files:
        head = p.read_text(encoding="utf-8")[:600]
        if re.search(r"\*\*Status:\*\*\s*OPEN", head):
            m = re.match(r"ADR-(\d+)", p.stem)
            if m:
                open_adrs.append(m.group(1))

    parts: list[str] = []
    parts.append("# Kosmos v25 — Consolidated Architecture Decision Records\n")
    parts.append(
        f"**Single-file bundle** of all {total_adrs} ADRs for Kosmos v25 plus the ADR index. "
        "Ordered by ID; every original filename is preserved as a section header so the file "
        "can be split back into individual ADR files if needed.\n"
    )
    if open_adrs:
        parts.append(
            "**Only OPEN ADR(s) in v25:** "
            + ", ".join(f"ADR-{n}" for n in open_adrs)
            + ". All others are Ratified or Ratified v25.\n"
        )
    else:
        parts.append("**No OPEN ADRs remain in v25.** All ADRs are Ratified or Ratified v25.\n")
    parts.append("---\n")

    readme = ADR_DIR / "README.md"
    parts.append("## FILE: `adrs/README.md`\n")
    parts.append(readme.read_text(encoding="utf-8").rstrip() + "\n")
    parts.append("---\n")

    for p in files:
        rel = f"adrs/{p.name}"
        parts.append(f"## FILE: `{rel}`\n")
        parts.append(p.read_text(encoding="utf-8").rstrip() + "\n")
        parts.append("---\n")

    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {total_adrs} ADRs)")


if __name__ == "__main__":
    main()
