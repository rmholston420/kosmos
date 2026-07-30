# Tree-sitter Tag Queries — Vendored from Aider

These `.scm` files are Tree-sitter tag queries vendored **verbatim** from
[Aider-AI/aider](https://github.com/Aider-AI/aider) at commit
`5dc9490bb35f` (2026-05-22). They are declarative Tree-sitter query DSL,
not Python source, and are included here under their upstream
Apache-2.0 license.

## Files

| File | Upstream path | Purpose |
|---|---|---|
| `python-tags.scm` | `aider/queries/tree-sitter-language-pack/python-tags.scm` | Python definitions/references |
| `javascript-tags.scm` | `aider/queries/tree-sitter-language-pack/javascript-tags.scm` | JS definitions/references |
| `typescript-tags.scm` | `aider/queries/tree-sitter-languages/typescript-tags.scm` | TS definitions/references |
| `rust-tags.scm` | `aider/queries/tree-sitter-language-pack/rust-tags.scm` | Rust definitions/references |
| `go-tags.scm` | `aider/queries/tree-sitter-language-pack/go-tags.scm` | Go definitions/references |
| `bash-tags.scm` | `aider/queries/tree-sitter-language-pack/bash-tags.scm` | Bash definitions/references |

## License

Apache License 2.0, © the Aider contributors. See
<https://github.com/Aider-AI/aider/blob/main/LICENSE.txt>.

## Modifications

None. Files are byte-for-byte upstream.

## Kosmos context

Consumed by `plugins/tektos/repomap/tags.py` via the `queries/` directory
lookup. Reimplementing these tag definitions ourselves would duplicate
work that upstream contributors performed under a permissive license;
Kosmos's ADR-020 vendoring precedent covers "verbatim declarative
content when the alternative is line-by-line re-derivation".

Related ADR: **ADR-038** (Stage 3.3 · aider repomap pattern-vendor).
