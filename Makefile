.PHONY: help test stage1-gate eval-gate

PY := .venv/bin/python

help:
	@echo "Kosmos make targets:"
	@echo "  test           Run the full pytest suite"
	@echo "  stage1-gate    Run the Stage-1 exit gate (Build-Sequence §1.15 DoD)"
	@echo "  eval-gate      Run the Pier eval-harness smoke fixture (Stage 3.8, ADR-042)"

test:
	$(PY) -m pytest

stage1-gate:
	$(PY) scripts/stage1_gate.py

eval-gate:
	$(PY) scripts/pier_eval.py \
		--task plugins/tektos/eval/tasks/tektos-plan-execution-smoke \
		--agent nop --env docker
