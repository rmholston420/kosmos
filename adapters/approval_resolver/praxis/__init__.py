"""Praxis-backed adapter for ``ports.approval.ApprovalResolverPort``.

Kernel wiring binds :class:`PraxisApprovalResolverAdapter` to
:class:`ports.approval.ApprovalResolverPort` at boot.
"""

from .adapter import PraxisApprovalResolverAdapter

__all__ = ["PraxisApprovalResolverAdapter"]
