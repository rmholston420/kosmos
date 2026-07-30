"""Manifest loader for the DeepSWE corpus (Stage 3.9, ADR-007-DeepSWE).

Reads ``manifest.toml`` next to this module, validates every subset
entry against the permissive-license allowlist, and returns typed
:class:`DeepSweSubsetEntry` rows. Rejects on:

* missing required keys
* unknown or copyleft SPDX id
* corpus name mismatch
* subset size mismatch vs. ``[corpus] subset_size``
* upstream commit mismatch vs. :data:`.policy.DEEPSWE_UPSTREAM_COMMIT`

No network I/O and no side effects — this is a pure parse used by the
fast unit tier.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .models import DeepSweSubsetEntry
from .policy import (
    DEEPSWE_CORPUS_NAME,
    DEEPSWE_PERMISSIVE_LICENSES,
    DEEPSWE_SUBSET_SIZE,
    DEEPSWE_UPSTREAM_COMMIT,
    DEEPSWE_UPSTREAM_LICENSE,
    DEEPSWE_UPSTREAM_REPO,
)

__all__ = [
    "DeepSweCorpus",
    "DeepSweManifestError",
    "load_deepswe_manifest",
]


class DeepSweManifestError(ValueError):
    """Raised when ``manifest.toml`` is malformed or violates policy."""


class DeepSweCorpus:
    """Wraps a parsed manifest and its subset entries.

    Kept as a plain class (not a frozen dataclass) so it can carry
    small helpers without inflating the value objects.
    """

    def __init__(
        self,
        *,
        manifest_path: Path,
        upstream_repo: str,
        upstream_commit: str,
        upstream_license: str,
        corpus_total_tasks: int,
        sample_seed: int,
        subset_size: int,
        subset: tuple[DeepSweSubsetEntry, ...],
    ) -> None:
        self.manifest_path = manifest_path
        self.upstream_repo = upstream_repo
        self.upstream_commit = upstream_commit
        self.upstream_license = upstream_license
        self.corpus_total_tasks = corpus_total_tasks
        self.sample_seed = sample_seed
        self.subset_size = subset_size
        self.subset = subset

    @property
    def task_ids(self) -> tuple[str, ...]:
        return tuple(entry.task_id for entry in self.subset)

    def language_mix(self) -> dict[str, int]:
        """Return a ``{language: count}`` map for the subset."""
        out: dict[str, int] = {}
        for entry in self.subset:
            out[entry.language] = out.get(entry.language, 0) + 1
        return out


_REQUIRED_SUBSET_KEYS = (
    "task_id",
    "language",
    "upstream_repo",
    "upstream_owner",
    "upstream_repo_name",
    "base_commit",
    "spdx_license",
)


def _default_manifest_path() -> Path:
    """Return the on-disk path to ``manifest.toml`` next to this module."""
    return Path(__file__).with_name("manifest.toml")


def _parse_subset_row(row: Any, *, index: int) -> DeepSweSubsetEntry:
    if not isinstance(row, dict):
        raise DeepSweManifestError(
            f"[[subset]] entry {index} is not a table: {type(row).__name__}"
        )
    missing = [key for key in _REQUIRED_SUBSET_KEYS if key not in row]
    if missing:
        raise DeepSweManifestError(
            f"[[subset]] entry {index} missing required keys: {missing}"
        )
    for key in _REQUIRED_SUBSET_KEYS:
        if not isinstance(row[key], str) or not row[key]:
            raise DeepSweManifestError(
                f"[[subset]] entry {index} key {key!r} must be a non-empty string"
            )
    spdx = row["spdx_license"]
    if spdx not in DEEPSWE_PERMISSIVE_LICENSES:
        raise DeepSweManifestError(
            f"[[subset]] entry {index} task_id={row['task_id']!r} "
            f"spdx_license={spdx!r} is not in the permissive allowlist "
            f"{sorted(DEEPSWE_PERMISSIVE_LICENSES)}. Add a superseding ADR "
            "before including a copyleft or source-available upstream."
        )
    return DeepSweSubsetEntry(
        task_id=row["task_id"],
        language=row["language"],
        upstream_repo=row["upstream_repo"],
        upstream_owner=row["upstream_owner"],
        upstream_repo_name=row["upstream_repo_name"],
        base_commit=row["base_commit"],
        spdx_license=spdx,
    )


def load_deepswe_manifest(
    manifest_path: Path | None = None,
) -> DeepSweCorpus:
    """Parse the DeepSWE manifest and return a validated :class:`DeepSweCorpus`.

    Args:
        manifest_path: Optional override, primarily for tests. Defaults
            to ``manifest.toml`` next to this module.

    Returns:
        A :class:`DeepSweCorpus` whose ``subset`` tuple is length
        :data:`.policy.DEEPSWE_SUBSET_SIZE` and whose every entry has a
        SPDX id in :data:`.policy.DEEPSWE_PERMISSIVE_LICENSES`.

    Raises:
        DeepSweManifestError: manifest missing, malformed, or policy
            violation (unknown SPDX id, size mismatch, commit mismatch).
    """
    resolved = manifest_path or _default_manifest_path()
    if not resolved.is_file():
        raise DeepSweManifestError(f"DeepSWE manifest not found: {resolved}")
    try:
        data = tomllib.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise DeepSweManifestError(
            f"Failed to parse DeepSWE manifest {resolved}: {exc}"
        ) from exc

    corpus_block = data.get("corpus")
    if not isinstance(corpus_block, dict):
        raise DeepSweManifestError("manifest.toml missing [corpus] table")
    for key in (
        "name",
        "upstream_repo",
        "upstream_commit",
        "upstream_license",
        "corpus_total_tasks",
        "sample_seed",
        "subset_size",
    ):
        if key not in corpus_block:
            raise DeepSweManifestError(f"[corpus] missing key: {key!r}")

    if corpus_block["name"] != DEEPSWE_CORPUS_NAME:
        raise DeepSweManifestError(
            f"[corpus] name mismatch: got {corpus_block['name']!r}, "
            f"expected {DEEPSWE_CORPUS_NAME!r}"
        )
    if corpus_block["upstream_repo"] != DEEPSWE_UPSTREAM_REPO:
        raise DeepSweManifestError(
            f"[corpus] upstream_repo mismatch: got {corpus_block['upstream_repo']!r}, "
            f"expected {DEEPSWE_UPSTREAM_REPO!r}"
        )
    if corpus_block["upstream_commit"] != DEEPSWE_UPSTREAM_COMMIT:
        raise DeepSweManifestError(
            f"[corpus] upstream_commit mismatch: got {corpus_block['upstream_commit']!r}, "
            f"expected {DEEPSWE_UPSTREAM_COMMIT!r}"
        )
    if corpus_block["upstream_license"] != DEEPSWE_UPSTREAM_LICENSE:
        raise DeepSweManifestError(
            f"[corpus] upstream_license mismatch: got {corpus_block['upstream_license']!r}, "
            f"expected {DEEPSWE_UPSTREAM_LICENSE!r}"
        )

    subset_raw = data.get("subset")
    if not isinstance(subset_raw, list) or not subset_raw:
        raise DeepSweManifestError("manifest.toml missing or empty [[subset]] array")

    entries = tuple(
        _parse_subset_row(row, index=i) for i, row in enumerate(subset_raw)
    )

    declared_size = corpus_block["subset_size"]
    if not isinstance(declared_size, int) or declared_size <= 0:
        raise DeepSweManifestError(
            f"[corpus] subset_size must be a positive int, got {declared_size!r}"
        )
    if declared_size != DEEPSWE_SUBSET_SIZE:
        raise DeepSweManifestError(
            f"[corpus] subset_size {declared_size} does not match locked "
            f"DEEPSWE_SUBSET_SIZE={DEEPSWE_SUBSET_SIZE}"
        )
    if len(entries) != declared_size:
        raise DeepSweManifestError(
            f"[[subset]] length {len(entries)} does not match "
            f"[corpus] subset_size {declared_size}"
        )
    if len(set(entry.task_id for entry in entries)) != len(entries):
        raise DeepSweManifestError(
            "[[subset]] contains duplicate task_id entries; each row must be unique"
        )

    return DeepSweCorpus(
        manifest_path=resolved,
        upstream_repo=corpus_block["upstream_repo"],
        upstream_commit=corpus_block["upstream_commit"],
        upstream_license=corpus_block["upstream_license"],
        corpus_total_tasks=int(corpus_block["corpus_total_tasks"]),
        sample_seed=int(corpus_block["sample_seed"]),
        subset_size=declared_size,
        subset=entries,
    )
