# Delta for tektos-ui-templates

## ADDED Requirements

### Requirement: Module-private escape-field helper

`plugins/tektos/ui/templates.py` SHALL expose a module-private helper
`_escape_record_fields(record: ApprovalRecord) -> tuple[str, str, str, str]`
returning the four HTML-escaped strings `(approval_id, change_id, tier, status)`
in that order.

#### Scenario: Helper returns HTML-escaped tuple
- GIVEN an `ApprovalRecord` with `approval_id="a-1"`, `intention_id="tektos.plan.change-42"`, `tier=HUMAN_REVIEW`, `status=PENDING`
- WHEN `_escape_record_fields(record)` is called
- THEN the return value is a 4-tuple of strings
- AND the first element equals `"a-1"`
- AND the second element equals `"change-42"`
- AND the third element equals `"human_review"`
- AND the fourth element equals `"pending"`

## MODIFIED Requirements

### Requirement: `render_pending_row` emits an approval row

`render_pending_row(record)` MUST continue to emit an HTML `<tr>` with
the escaped `approval_id`, `change_id`, `tier`, `status` and the HTMX
approve button as it did prior to Stage 3.12.

#### Scenario: Row shape unchanged
- GIVEN an `ApprovalRecord` at `HUMAN_REVIEW` / `PENDING`
- WHEN `render_pending_row(record)` is called
- THEN the returned string starts with `<tr id="row-`
- AND contains one HTMX-annotated `approve` button

### Requirement: `render_plan_detail` emits a plan-detail section

`render_plan_detail(record)` MUST continue to emit an HTML `<section>`
with the escaped `approval_id`, `change_id`, `tier`, `status`, and the
three HTMX-annotated buttons for approve, execute, diff as it did prior
to Stage 3.12.

#### Scenario: Detail shape unchanged
- GIVEN an `ApprovalRecord` at `HUMAN_REVIEW` / `PENDING`
- WHEN `render_plan_detail(record)` is called
- THEN the returned string contains `<section id="plan-detail-`
- AND contains three HTMX-annotated buttons

## REMOVED Requirements

### Requirement: In-lined escape block in row/detail renderers

The duplicated 4-line escape block that appeared in `render_pending_row`
and `render_plan_detail` is REMOVED. Both call sites now call
`_escape_record_fields` and receive the tuple.
