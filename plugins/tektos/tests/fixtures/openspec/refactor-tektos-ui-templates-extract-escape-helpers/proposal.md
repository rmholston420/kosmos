# Proposal: Extract escape helpers in Tektos UI templates

## Intent

`plugins/tektos/ui/templates.py` currently duplicates a 4-line block that
projects an `ApprovalRecord` into four HTML-escaped strings
(`approval_id`, `change_id`, `tier`, `status`). The duplication appears
in `render_pending_row` (line 112) and `render_plan_detail` (line 146).
The projection is identical in both call sites and the projection
convention (`ApprovalRecord` → 4 escaped strings) is currently
implicit — it exists only as a repeated recipe, not as a named surface.

## Scope

- Introduce a module-private helper `_escape_record_fields(record: ApprovalRecord) -> tuple[str, str, str, str]` returning `(approval_id, change_id, tier, status)`, all HTML-escaped.
- Rewrite `render_pending_row` to call the helper.
- Rewrite `render_plan_detail` to call the helper.
- Preserve every existing test assertion in `plugins/tektos/tests/test_tektos_ui.py`.
- No changes to any public function signature.
- No changes to any other file in `plugins/tektos/ui/`.

## Approach

Standard extract-method refactor. The helper lives at module scope
just after `_change_id_from_intention` and before `render_pending_row`.
Both call sites replace 4 statements with a single tuple unpack:

```python
approval_id, change_id, tier, status = _escape_record_fields(record)
```

## Out of scope

- Extracting any other duplication in the module.
- Renaming or moving the callers.
- Changing the escape strategy (still `html.escape`).
- Any change to `plugins/tektos/ui/server.py` or `plugins/tektos/ui/policy.py`.
