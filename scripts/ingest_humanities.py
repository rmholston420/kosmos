"""SuttaCentral Bilara humanities corpus ingest CLI (Stage 4.5 · ADR-050).

Regenerates
`adapters/memory/dozerdb/corpora/humanities_bilara/fixtures/humanities_bilara.jsonl`
from a pinned upstream commit SHA of `github.com/suttacentral/bilara-data`.

Not vendored code — this is workspace-local tooling. Bilara's segment-keyed
translation JSON lands as data in the fixture; no upstream code is imported at
runtime.

Scope at Stage 4.5:
- Three Khuddaka Nikaya publications by Bhikkhu Sujato (English):
  scpub7=Dhammapada (`kn/dhp`), scpub19=Khuddakapatha (`kn/kp`),
  scpub86=Cariyapitaka (`kn/cp`).
- Each English translation is mirrored by its Pali root under
  `root/pli/ms/sutta/kn/<subdir>/`.
- Companion metadata (`_author.json`, `_publication.json`) is used to
  materialize CIDOC-CRM E21_Person actor records + P94_was_created_by /
  P73_has_translation typed edges. Actors are emitted as their own
  MemoryPort records so the typed-link CorpusEdge machinery from
  Stage 4.4 can resolve source and target inside the same corpus.

Usage:
    # From GitHub via gh (default; no local checkout required):
    python scripts/ingest_humanities.py \\
        --sha 3c93d1cea80fdebcefb777c8724c35bd971f360a

    # Or from a local checkout of the upstream repo:
    python scripts/ingest_humanities.py \\
        --sha 3c93d1cea80fdebcefb777c8724c35bd971f360a \\
        --via checkout --source /path/to/bilara-data-checkout

Each fixture record is one CorpusFact-shaped JSON row. Three subject
namespaces are used:

    bilara/root/<uid>         Pali root text file
    bilara/translation/<uid>  English translation of that root
    bilara/actor/<uid>        Translator / editor E21_Person actor

Typed edges (materialized inside `attributes.references` on the
translation records + the actor records to keep the edge writer single-
sided; edge kind matches CIDOC-CRM property URI):

    P73_has_translation           root -> translation  (emitted on translation record with kind="P73_is_translation_of" pointing back to root)
    P94_was_created_by            translation -> actor (emitted on translation record)
    P148_has_component            publication -> file  (each file inside a
                                                        publication references its publication uid)

The corpus loader wires these into `CorpusEdge` records at construction
time exactly the same way Stage 4.4's Superpowers loader does.

ADR-007 respected — this CLI never imports anything under `plugins/`.
ADR-008 respected — no Bilara code enters `vendor/` or `adapters/`
package code; only translation JSON + metadata lands as fixture data.

License posture:
- SuttaCentral / Bilara translations: Creative Commons Zero (CC0, public
  domain dedication) per upstream `LICENSE.md`.
- Pali source texts: Mahasangiti edition, public domain.
- Both licenses permit unrestricted redistribution; each record carries
  `attributes.license` for downstream audit.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "adapters"
    / "memory"
    / "dozerdb"
    / "corpora"
    / "humanities_bilara"
    / "fixtures"
    / "humanities_bilara.jsonl"
)

UPSTREAM_REPO = "suttacentral/bilara-data"
UPSTREAM_URL = "https://github.com/suttacentral/bilara-data"

# Stage 4.5 target slice — three KN publications by Sujato, English.
TARGET_PUBLICATIONS = ("scpub7", "scpub19", "scpub86")
TARGET_TRANSLATION_LANG = "en"
TARGET_TRANSLATOR = "sujato"
TARGET_KN_SUBDIRS = ("dhp", "kp", "cp")

# Root path prefixes (repo-relative).
TRANSLATION_PREFIX = f"translation/{TARGET_TRANSLATION_LANG}/{TARGET_TRANSLATOR}/sutta/kn/"
ROOT_PREFIX = "root/pli/ms/sutta/kn/"

# CIDOC-CRM property URIs used as CorpusEdge kinds.
KIND_IS_TRANSLATION_OF = "P73_is_translation_of"
KIND_WAS_CREATED_BY = "P94_was_created_by"
KIND_HAS_COMPONENT_OF = "P148i_is_component_of"  # inverse of P148_has_component

# Bilara text licenses (per upstream LICENSE.md + edition metadata).
LICENSE_TRANSLATION = "CC0-1.0"
LICENSE_ROOT_PALI = "public-domain"  # Mahasangiti edition


@dataclass(frozen=True, slots=True)
class BilaraFile:
    """One upstream JSON file at the pinned SHA."""

    path: str  # repo-relative, e.g. "translation/en/sujato/sutta/kn/dhp/dhp1-20_translation-en-sujato.json"
    kind: str  # "translation" | "root"
    subdir: str  # e.g. "dhp" | "kp" | "cp"
    uid: str  # bilara segment uid stem, e.g. "dhp1-20"
    body_json: dict  # segment-keyed dict, decoded


@dataclass(frozen=True, slots=True)
class ActorRecord:
    """One CIDOC-CRM E21_Person actor from _author.json."""

    uid: str
    display_name: str
    author_type: str  # "translator" | "editor" | etc.


@dataclass(frozen=True, slots=True)
class PublicationRecord:
    """One publication from _publication.json (target slice only)."""

    uid: str  # "scpub7" etc.
    text_uid: str  # "dhp" / "kp" / "cp"
    author_uid: str  # "sujato"
    source_url: str
    metadata: dict = field(default_factory=dict)  # extra fields preserved for audit


# ------------------------------------------------------------------ #
# gh api fetchers                                                     #
# ------------------------------------------------------------------ #


def _gh_get_json(endpoint: str) -> dict | list:
    raw = subprocess.check_output(["gh", "api", endpoint], text=True)
    return json.loads(raw)


def _gh_get_file_body(path: str, sha: str) -> str:
    """Base64-decoded file body via `gh api`."""
    blob = _gh_get_json(f"repos/{UPSTREAM_REPO}/contents/{path}?ref={sha}")
    assert isinstance(blob, dict)
    return base64.b64decode(blob["content"]).decode("utf-8")


def _gh_list_json_files(dir_path: str, sha: str) -> list[str]:
    """List *.json files under a directory (non-recursive) at the pinned SHA."""
    entries = _gh_get_json(f"repos/{UPSTREAM_REPO}/contents/{dir_path}?ref={sha}")
    assert isinstance(entries, list)
    return sorted(
        f"{dir_path}/{e['name']}"
        for e in entries
        if e.get("type") == "file" and e["name"].endswith(".json")
    )


# ------------------------------------------------------------------ #
# checkout fetchers                                                   #
# ------------------------------------------------------------------ #


def _co_file_body(source: Path, path: str, sha: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source), "show", f"{sha}:{path}"], text=True,
    )


def _co_list_files(source: Path, prefix: str, sha: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "-C", str(source), "ls-tree", "-r", "--name-only", sha, prefix],
        text=True,
    )
    return sorted(p for p in out.splitlines() if p.endswith(".json"))


# ------------------------------------------------------------------ #
# fetch drivers                                                       #
# ------------------------------------------------------------------ #


def _fetch_all(
    sha: str,
    *,
    via: str,
    source: Path | None,
) -> tuple[dict, dict, list[BilaraFile], str]:
    """Return (author_json, publication_json, files, commit_iso).

    Only files in the Stage 4.5 target slice are returned.
    """
    if via == "gh":
        author_json = _gh_get_file_body("_author.json", sha)
        publication_json = _gh_get_file_body("_publication.json", sha)
        commit = _gh_get_json(f"repos/{UPSTREAM_REPO}/git/commits/{sha}")
        assert isinstance(commit, dict)
        commit_iso = commit["author"]["date"]
    elif via == "checkout":
        assert source is not None
        subprocess.check_call(
            ["git", "-C", str(source), "cat-file", "-e", f"{sha}^{{commit}}"],
        )
        author_json = _co_file_body(source, "_author.json", sha)
        publication_json = _co_file_body(source, "_publication.json", sha)
        commit_iso = subprocess.check_output(
            ["git", "-C", str(source), "show", "-s", "--format=%aI", sha], text=True,
        ).strip()
    else:  # pragma: no cover
        raise ValueError(f"unknown via: {via}")

    authors = json.loads(author_json)
    publications = json.loads(publication_json)

    files: list[BilaraFile] = []
    for subdir in TARGET_KN_SUBDIRS:
        # Translations
        t_prefix = f"{TRANSLATION_PREFIX}{subdir}"
        r_prefix = f"{ROOT_PREFIX}{subdir}"
        if via == "gh":
            t_paths = _gh_list_json_files(t_prefix, sha)
            r_paths = _gh_list_json_files(r_prefix, sha)
        else:
            assert source is not None
            t_paths = _co_list_files(source, t_prefix, sha)
            r_paths = _co_list_files(source, r_prefix, sha)

        for p in t_paths:
            uid = Path(p).stem.split("_")[0]  # "dhp1-20_translation-en-sujato" -> "dhp1-20"
            body = (
                _gh_get_file_body(p, sha)
                if via == "gh"
                else _co_file_body(source, p, sha)  # type: ignore[arg-type]
            )
            files.append(
                BilaraFile(
                    path=p,
                    kind="translation",
                    subdir=subdir,
                    uid=uid,
                    body_json=json.loads(body),
                ),
            )
        for p in r_paths:
            uid = Path(p).stem.split("_")[0]
            body = (
                _gh_get_file_body(p, sha)
                if via == "gh"
                else _co_file_body(source, p, sha)  # type: ignore[arg-type]
            )
            files.append(
                BilaraFile(
                    path=p,
                    kind="root",
                    subdir=subdir,
                    uid=uid,
                    body_json=json.loads(body),
                ),
            )
    return authors, publications, files, commit_iso


# ------------------------------------------------------------------ #
# record builders                                                     #
# ------------------------------------------------------------------ #


def _event_id_translation(uid: str) -> str:
    return f"bilara.translation.{TARGET_TRANSLATION_LANG}.{TARGET_TRANSLATOR}.{uid}"


def _event_id_root(uid: str) -> str:
    return f"bilara.root.pli.ms.{uid}"


def _event_id_actor(author_uid: str) -> str:
    return f"bilara.actor.{author_uid}"


def _flatten_segments(seg_dict: dict) -> str:
    """Concatenate segment-keyed values in insertion order (dict is
    JSON-key-ordered on Python 3.7+). Preserves per-segment whitespace
    that Bilara ships (each value already ends with a trailing space
    when a joining space is expected)."""
    return "".join(str(v) for v in seg_dict.values())


def _build_actor_records(
    authors: dict, sha: str, commit_iso: str,
) -> tuple[list[dict], set[str]]:
    """Emit actor records for translators referenced by our target
    publications. Returns (records, target_author_uids)."""
    # Only emit actors we actually use (translators of our target slice).
    target_uids = {TARGET_TRANSLATOR}
    records: list[dict] = []
    for uid in sorted(target_uids):
        meta = authors.get(uid, {})
        records.append({
            "event_id": _event_id_actor(uid),
            "subject": f"bilara/actor/{uid}",
            "predicate": "bilara.actor.declared",
            "object": uid,
            "as_of": commit_iso,
            "provenance": f"bilara@{sha}:_author.json#{uid}",
            "confidence": 1.0,
            "attributes": {
                "author_uid": uid,
                "author_name": meta.get("name", uid),
                "author_type": meta.get("type", "unknown"),
                "crm_class": "E21_Person",
                "source_commit": sha,
                "source_path": "_author.json",
                "license": LICENSE_TRANSLATION,
                "upstream_url": f"{UPSTREAM_URL}/blob/{sha}/_author.json",
                "references": [],
            },
        })
    return records, target_uids


def _build_publication_index(
    publications: dict,
) -> dict[str, PublicationRecord]:
    """Extract the target-slice publication metadata (uid -> record)."""
    idx: dict[str, PublicationRecord] = {}
    for pub_uid in TARGET_PUBLICATIONS:
        p = publications.get(pub_uid)
        if not p:
            raise SystemExit(f"error: publication {pub_uid} missing from _publication.json")
        text_uid = p.get("text_uid") or p.get("source_url", "").rstrip("/").split("/")[-1]
        idx[pub_uid] = PublicationRecord(
            uid=pub_uid,
            text_uid=text_uid,
            author_uid=p.get("author_uid", TARGET_TRANSLATOR),
            source_url=p.get("source_url", ""),
            metadata={
                k: v
                for k, v in p.items()
                if k in ("publication_date", "publication_number", "creator_uid", "text_description")
            },
        )
    return idx


def _build_root_records(
    files: Iterable[BilaraFile], sha: str, commit_iso: str,
) -> list[dict]:
    records: list[dict] = []
    for f in files:
        if f.kind != "root":
            continue
        body_text = _flatten_segments(f.body_json)
        records.append({
            "event_id": _event_id_root(f.uid),
            "subject": f"bilara/root/{f.uid}",
            "predicate": "bilara.root.declared",
            "object": f.path,
            "as_of": commit_iso,
            "provenance": f"bilara@{sha}:{f.path}",
            "confidence": 1.0,
            "attributes": {
                "bilara_uid": f.uid,
                "root_lang": "pli",
                "edition": "ms",  # Mahasangiti
                "crm_class": "E33_Linguistic_Object",
                "subdir": f.subdir,
                "body": body_text,
                "segment_count": len(f.body_json),
                "source_commit": sha,
                "source_path": f.path,
                "license": LICENSE_ROOT_PALI,
                "upstream_url": f"{UPSTREAM_URL}/blob/{sha}/{f.path}",
                "references": [],
            },
        })
    return records


def _translation_publication(
    subdir: str, pub_idx: dict[str, PublicationRecord],
) -> PublicationRecord:
    for pub in pub_idx.values():
        if pub.text_uid == subdir:
            return pub
    raise SystemExit(f"error: no target publication maps to subdir {subdir}")


def _build_translation_records(
    files: Iterable[BilaraFile],
    sha: str,
    commit_iso: str,
    pub_idx: dict[str, PublicationRecord],
    known_event_ids: set[str],
) -> list[dict]:
    records: list[dict] = []
    for f in files:
        if f.kind != "translation":
            continue
        body_text = _flatten_segments(f.body_json)
        pub = _translation_publication(f.subdir, pub_idx)
        root_event_id = _event_id_root(f.uid)
        actor_event_id = _event_id_actor(pub.author_uid)

        # Typed edges — each targets an event_id that MUST resolve inside
        # the same corpus. We only emit edges whose target we can verify
        # in the fixture set.
        refs: list[dict] = []
        if root_event_id in known_event_ids:
            refs.append({
                "kind": KIND_IS_TRANSLATION_OF,
                "target_path": _root_path_for_uid(f.uid, f.subdir),
                "target_event_id": root_event_id,
                "anchor_text": f"Pali root of {f.uid}",
            })
        if actor_event_id in known_event_ids:
            refs.append({
                "kind": KIND_WAS_CREATED_BY,
                "target_path": "_author.json",
                "target_event_id": actor_event_id,
                "anchor_text": pub.author_uid,
            })

        records.append({
            "event_id": _event_id_translation(f.uid),
            "subject": f"bilara/translation/{f.uid}",
            "predicate": "bilara.translation.declared",
            "object": f.path,
            "as_of": commit_iso,
            "provenance": f"bilara@{sha}:{f.path}",
            "confidence": 1.0,
            "attributes": {
                "bilara_uid": f.uid,
                "translation_lang": TARGET_TRANSLATION_LANG,
                "translator_uid": pub.author_uid,
                "publication_uid": pub.uid,
                "publication_text_uid": pub.text_uid,
                "publication_source_url": pub.source_url,
                "publication_metadata": pub.metadata,
                "crm_class": "E33_Linguistic_Object",
                "subdir": f.subdir,
                "body": body_text,
                "segment_count": len(f.body_json),
                "source_commit": sha,
                "source_path": f.path,
                "license": LICENSE_TRANSLATION,
                "upstream_url": f"{UPSTREAM_URL}/blob/{sha}/{f.path}",
                "references": refs,
            },
        })
    return records


def _root_path_for_uid(uid: str, subdir: str) -> str:
    return f"{ROOT_PREFIX}{subdir}/{uid}_root-pli-ms.json"


# ------------------------------------------------------------------ #
# main                                                                #
# ------------------------------------------------------------------ #


def build(sha: str, *, via: str, source: Path | None) -> list[dict]:
    authors, publications, files, commit_iso = _fetch_all(sha, via=via, source=source)

    if not files:
        raise SystemExit(f"error: no target files found at {sha}")

    pub_idx = _build_publication_index(publications)
    actor_records, _ = _build_actor_records(authors, sha, commit_iso)
    root_records = _build_root_records(files, sha, commit_iso)

    known_event_ids: set[str] = {r["event_id"] for r in actor_records + root_records}
    translation_records = _build_translation_records(
        files, sha, commit_iso, pub_idx, known_event_ids,
    )

    # Emit in a stable order for byte-reproducible fixtures:
    # actors first, then roots, then translations, each sorted by event_id.
    all_records = (
        sorted(actor_records, key=lambda r: r["event_id"])
        + sorted(root_records, key=lambda r: r["event_id"])
        + sorted(translation_records, key=lambda r: r["event_id"])
    )
    return all_records


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Ingest SuttaCentral Bilara humanities corpus into Kosmos MemoryPort fixture.",
    )
    p.add_argument("--sha", required=True, help="Pinned upstream commit SHA.")
    p.add_argument(
        "--via",
        choices=("gh", "checkout"),
        default="gh",
        help="Fetch mode: `gh api` (default) or local checkout via --source.",
    )
    p.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Local upstream checkout path when --via=checkout.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=FIXTURE_PATH,
        help=f"Output JSONL path (default: {FIXTURE_PATH}).",
    )
    args = p.parse_args(argv)

    if args.via == "checkout" and args.source is None:
        p.error("--via=checkout requires --source /path/to/upstream")

    records = build(args.sha, via=args.via, source=args.source)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    edge_count = sum(len(r["attributes"].get("references", [])) for r in records)
    actor_count = sum(1 for r in records if r["subject"].startswith("bilara/actor/"))
    root_count = sum(1 for r in records if r["subject"].startswith("bilara/root/"))
    trans_count = sum(1 for r in records if r["subject"].startswith("bilara/translation/"))
    print(
        f"wrote {len(records)} records "
        f"({actor_count} actor + {root_count} root + {trans_count} translation, "
        f"{edge_count} typed CIDOC-CRM edges) to {args.output} @ {args.sha[:12]}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
