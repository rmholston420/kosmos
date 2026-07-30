"""Phrouros error hierarchy (ADR-034).

Single-base :class:`PhrourosError` so callers can catch one type at the
plugin boundary.
"""

from __future__ import annotations


class PhrourosError(Exception):
    """Base class for every Phrouros-raised exception."""


class DetectorNotImplementedError(PhrourosError, NotImplementedError):
    """A skeleton detector's ``detect()`` was invoked before its real
    landing stage. Skeletons at Stage 2.3 (ModelSwapSloDetector,
    StubDegradationDetector, BusFactor1Detector) raise this to make the
    "registered but deferred" state observable in tests.

    Inherits from :class:`NotImplementedError` so a plain-Python
    ``except NotImplementedError`` still catches it.
    """


class AnomalyNotFoundError(PhrourosError, KeyError):
    """The requested :class:`AnomalyRecord` id was not in storage.

    Inherits from :class:`KeyError` for stdlib compatibility.
    """


class EngineNotRunningError(PhrourosError, RuntimeError):
    """Called a verb that requires the engine to be started (subscribed
    to the trace feed) before :meth:`PhrourosEngine.start`.
    """
