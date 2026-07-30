"""KernelNotificationAdapter — ADR-030 Stage 1.12 primary NotificationPort."""
from adapters.notification.kernel.adapter import (
    InProcessSink,
    KernelNotificationAdapter,
    NtfySink,
)

__all__ = ["InProcessSink", "KernelNotificationAdapter", "NtfySink"]
