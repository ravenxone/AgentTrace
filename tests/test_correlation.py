from agenttrace.correlation import correlate_session_events


def test_correlation_prefers_correlation_id_within_window() -> None:
    events = [
        {
            "source": "codex_cli",
            "source_event_id": "cx-1",
            "agent_id": "agent://worker-1",
            "identity_id": "spn://entra/spn-001",
            "session_id": "session://incident-1",
            "event_time": "2026-03-01T10:00:00Z",
            "ingest_time": "2026-03-01T10:00:01Z",
            "event_type": "command.run",
            "payload": {"correlation_id": "corr-9001"},
        },
        {
            "source": "entra_id",
            "source_event_id": "en-1",
            "agent_id": "agent://worker-1",
            "identity_id": "spn://entra/spn-001",
            "session_id": "session://incident-1",
            "event_time": "2026-03-01T09:59:45Z",
            "ingest_time": "2026-03-01T10:00:01Z",
            "event_type": "signin.success",
            "payload": {"correlation_id": "corr-9001"},
        },
    ]

    correlated = correlate_session_events(events=events, window_seconds=300)
    runtime = [event for event in correlated if event.get("role") == "runtime_action"][0]
    correlation = runtime["correlation"]

    assert correlation["status"] == "matched"
    assert correlation["confidence"] == "high"
    assert correlation["matched_event"]["source_event_id"] == "en-1"
    assert "correlation_id" in correlation["reason_codes"]
