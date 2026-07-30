# Tasks: Extract escape helpers in Tektos UI templates

## Implementation checklist

- [x] Identify the duplicated 4-line escape block in `render_pending_row` and `render_plan_detail`
- [x] Design the helper signature `_escape_record_fields(record) -> tuple[str, str, str, str]`
- [ ] Author `_escape_record_fields` at module scope
- [ ] Replace the duplicated block in `render_pending_row` with a tuple unpack
- [ ] Replace the duplicated block in `render_plan_detail` with a tuple unpack
- [ ] Confirm ruff + bandit + pytest still pass over `plugins/tektos/ui/templates.py`

## Validation

- [ ] `.venv/bin/ruff check plugins/tektos/ui/templates.py` exits 0
- [ ] `.venv/bin/bandit -q -c pyproject.toml -r plugins/tektos/ui/templates.py` exits 0
- [ ] `.venv/bin/pytest plugins/tektos/tests/test_tektos_ui.py` remains 24 passing (unchanged surface)
