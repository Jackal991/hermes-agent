"""Lease-wait lifecycle statuses must honour the interim-message mute."""

import pytest

from agent.conversation_compression import COMPACTION_DONE_STATUS
from agent.session_turn_lease_status import (
    SESSION_TURN_LEASE_RELOADING_STATUS,
    SESSION_TURN_LEASE_TIMEOUT_STATUS,
    SESSION_TURN_LEASE_WAITING_STATUS,
    session_turn_lease_waiting_again_status,
)
from gateway.config import Platform
from gateway.run import (
    _GATEWAY_RAW_TEXT_PLATFORMS,
    _prepare_gateway_status_message,
)

INTERIM_LEASE_LIFECYCLE_MESSAGES = [
    SESSION_TURN_LEASE_WAITING_STATUS,
    session_turn_lease_waiting_again_status(15),
    session_turn_lease_waiting_again_status(30),
    SESSION_TURN_LEASE_RELOADING_STATUS,
]

RAW_TEXT_SURFACES = sorted(_GATEWAY_RAW_TEXT_PLATFORMS)
HUMAN_CHAT_SURFACES = [
    platform
    for platform in Platform
    if platform.value not in _GATEWAY_RAW_TEXT_PLATFORMS
]
HUMAN_CHAT_SURFACES.append("irc")


@pytest.mark.parametrize("message", INTERIM_LEASE_LIFECYCLE_MESSAGES)
@pytest.mark.parametrize("platform", HUMAN_CHAT_SURFACES)
def test_lifecycle_lease_statuses_suppressed_when_interim_muted(platform, message):
    """interim_enabled=False must swallow the lifecycle lease-wait chatter."""
    assert (
        _prepare_gateway_status_message(
            platform, "lifecycle", message, interim_enabled=False
        )
        is None
    )


@pytest.mark.parametrize("message", INTERIM_LEASE_LIFECYCLE_MESSAGES)
@pytest.mark.parametrize("platform", HUMAN_CHAT_SURFACES)
def test_lifecycle_lease_statuses_flow_when_interim_enabled(platform, message):
    """interim_enabled=True (the default) keeps lifecycle messages flowing."""
    assert (
        _prepare_gateway_status_message(platform, "lifecycle", message)
        == message
    )


@pytest.mark.parametrize("platform", RAW_TEXT_SURFACES)
@pytest.mark.parametrize("message", INTERIM_LEASE_LIFECYCLE_MESSAGES)
def test_programmatic_surfaces_keep_raw_lease_status_when_interim_muted(
    platform, message
):
    """Raw/local/API surfaces are diagnostic channels, not chat delivery."""
    assert (
        _prepare_gateway_status_message(
            platform, "lifecycle", message, interim_enabled=False
        )
        == message
    )


@pytest.mark.parametrize("message", INTERIM_LEASE_LIFECYCLE_MESSAGES)
def test_lifecycle_classifier_is_exact_case_and_full_message(message):
    """Near-matches must not accidentally hide a real user-facing notice."""
    assert (
        _prepare_gateway_status_message(
            Platform.WHATSAPP,
            "lifecycle",
            f"{message} Please contact support if it persists.",
            interim_enabled=False,
        )
        == f"{message} Please contact support if it persists."
    )

    changed_case = message.replace("Hermes", "hermes").replace("Session", "session")
    assert changed_case != message
    assert (
        _prepare_gateway_status_message(
            Platform.WHATSAPP,
            "lifecycle",
            changed_case,
            interim_enabled=False,
        )
        == changed_case
    )


def test_lifecycle_gate_is_scoped_to_lifecycle_only():
    """An exact lease status is suppressed only for lifecycle events."""
    assert (
        _prepare_gateway_status_message(
            Platform.TELEGRAM,
            "warn",
            SESSION_TURN_LEASE_WAITING_STATUS,
            interim_enabled=False,
        )
        == SESSION_TURN_LEASE_WAITING_STATUS
    )


@pytest.mark.parametrize("platform", HUMAN_CHAT_SURFACES)
def test_compression_completion_passthrough_is_unchanged_when_interim_muted(platform):
    """The lease filter must not turn the separate compression contract off."""
    assert (
        _prepare_gateway_status_message(
            platform,
            "compacted",
            COMPACTION_DONE_STATUS,
            interim_enabled=False,
        )
        == COMPACTION_DONE_STATUS
    )


# Durable must-see lifecycle statuses that reach the gateway today and MUST
# keep flowing even when interim assistant messages are muted. These are
# emitted as ``lifecycle`` callbacks but are NOT lease-contention chatter:
# a blanket event_type=="lifecycle" gate would silently drop them — a
# regression this suite pins against.
DURABLE_LIFECYCLE_MESSAGES = [
    # Fallback-switch notice (run_agent._emit_pending_fallback_notice, ~line 1211).
    "↻ Switched to fallback: gpt-4o (openai)",
    # Terminal provider-failure notice, buffered via _buffer_status and
    # replayed via _emit_status on terminal flush.
    "❌ Connection to provider failed after 3 attempts. The provider may be "
    "experiencing issues — try again in a moment.",
]


@pytest.mark.parametrize("message", DURABLE_LIFECYCLE_MESSAGES)
@pytest.mark.parametrize("platform", HUMAN_CHAT_SURFACES)
def test_durable_lifecycle_statuses_flow_when_interim_muted(platform, message):
    """interim_enabled=False must NOT swallow durable lifecycle messages."""
    assert (
        _prepare_gateway_status_message(
            platform, "lifecycle", message, interim_enabled=False
        )
        == message
    )


@pytest.mark.parametrize("platform", HUMAN_CHAT_SURFACES)
def test_lease_timeout_warning_flows_when_interim_muted(platform):
    """The terminal lease timeout is a visible warning, not interim chatter."""
    assert (
        _prepare_gateway_status_message(
            platform,
            "warn",
            SESSION_TURN_LEASE_TIMEOUT_STATUS,
            interim_enabled=False,
        )
        == SESSION_TURN_LEASE_TIMEOUT_STATUS
    )
