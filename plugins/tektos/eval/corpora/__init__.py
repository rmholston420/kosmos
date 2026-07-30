"""Tektos eval corpora (Stage 3.9+).

Each corpus is a subpackage under :mod:`plugins.tektos.eval.corpora`. A
corpus vendors a *manifest* (source URL, upstream commit, filtered task
subset, per-task license notes) but not the task source itself — tasks
are fetched on-demand into ``.eval-cache/`` per ADR-007-DeepSWE.
"""
