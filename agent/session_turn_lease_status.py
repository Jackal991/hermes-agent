"""Shared user-facing statuses for cross-process session-turn leases.

The agent emits these while a durable conversation lease is held by another
Hermes process.  Gateways use the same definitions to distinguish transient
lease chatter from the visible terminal timeout warning and other durable
notices.  Keep this module dependency-free: it is imported by both the core
agent and the gateway.
"""

from __future__ import annotations

import re


SESSION_TURN_LEASE_WAITING_STATUS = (
    "⏳ Another Hermes process is using this session; "
    "waiting for it to finish before starting your turn..."
)
SESSION_TURN_LEASE_WAITING_AGAIN_TEMPLATE = (
    "⏳ Still waiting for the other Hermes process on this session ({seconds}s)..."
)
SESSION_TURN_LEASE_RELOADING_STATUS = "Session is free; loading the latest transcript..."
SESSION_TURN_LEASE_TIMEOUT_STATUS = (
    "⏳ Another Hermes process kept this session busy too long. Your message "
    "was not processed - wait for the other process to finish, then send it again."
)

_WAITING_AGAIN_PREFIX, _WAITING_AGAIN_SUFFIX = (
    SESSION_TURN_LEASE_WAITING_AGAIN_TEMPLATE.split("{seconds}")
)
_SESSION_TURN_LEASE_WAITING_AGAIN_RE = re.compile(
    re.escape(_WAITING_AGAIN_PREFIX) + r"[0-9]+" + re.escape(_WAITING_AGAIN_SUFFIX)
)


def session_turn_lease_waiting_again_status(seconds: int) -> str:
    """Format the periodic, transient cross-process lease-wait status."""
    return SESSION_TURN_LEASE_WAITING_AGAIN_TEMPLATE.format(seconds=int(seconds))


def is_session_turn_lease_interim_status(message: str) -> bool:
    """Return whether *message* is exactly a transient lease-wait status.

    This is deliberately exact-case and full-match.  The user-visible terminal
    timeout is not part of this set and must remain deliverable.
    """
    return (
        message in {
            SESSION_TURN_LEASE_WAITING_STATUS,
            SESSION_TURN_LEASE_RELOADING_STATUS,
        }
        or _SESSION_TURN_LEASE_WAITING_AGAIN_RE.fullmatch(message) is not None
    )
