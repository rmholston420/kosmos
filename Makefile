.PHONY: help test stage1-gate eval-gate deepswe-fetch deepswe-gate ingest-doc ui-serve

PY := .venv/bin/python

help:
	@echo "Kosmos make targets:"
	@echo "  test           Run the full pytest suite"
	@echo "  stage1-gate    Run the Stage-1 exit gate (Build-Sequence §1.15 DoD)"
	@echo "  eval-gate      Run the Pier eval-harness smoke fixture (Stage 3.8, ADR-042)"
	@echo "  deepswe-fetch  Hydrate the pinned DeepSWE subset into .eval-cache/ (Stage 3.9)"
	@echo "  deepswe-gate   Run the DeepSWE subset through Pier (Stage 3.9, ADR-007-DeepSWE)"
	@echo "  ingest-doc     Ingest one document via docling + DataPort (Stage 3.10, ADR-043)"
	@echo "  ui-serve       Serve the Tektos UI HTMX dashboard on 127.0.0.1:8765 (Stage 3.11, ADR-045)"

test:
	$(PY) -m pytest

stage1-gate:
	$(PY) scripts/stage1_gate.py

eval-gate:
	$(PY) scripts/pier_eval.py \
		--task plugins/tektos/eval/tasks/tektos-plan-execution-smoke \
		--agent nop --env docker

deepswe-fetch:
	$(PY) scripts/deepswe_fetch.py --cache-dir .eval-cache/deepswe

deepswe-gate: deepswe-fetch
	$(PY) scripts/deepswe_run.py \
		--cache-dir .eval-cache/deepswe \
		--agent nop --env docker

ingest-doc:
	$(PY) scripts/docling_ingest.py \
		--path plugins/tektos/tests/fixtures/docling/sample.html \
		--out-root .ingest-cache/docling

ui-serve:
	$(PY) scripts/tektos_ui.py
