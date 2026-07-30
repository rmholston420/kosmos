.PHONY: help test stage1-gate

PY := .venv/bin/python

help:
	@echo "Kosmos make targets:"
	@echo "  test           Run the full pytest suite"
	@echo "  stage1-gate    Run the Stage-1 exit gate (Build-Sequence §1.15 DoD)"

test:
	$(PY) -m pytest

stage1-gate:
	$(PY) scripts/stage1_gate.py
