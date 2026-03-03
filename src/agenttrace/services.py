from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agenttrace.correlation import correlate_session_events, summarize_correlations
from agenttrace.models import utc_now_iso
from agenttrace.storage.sqlite_index import SQLiteIndex


def build_session_timeline(index: SQLiteIndex, session_id: str) -> list[dict[str, Any]]:
    return index.session_events(session_id=session_id)


def build_correlated_timeline(
    index: SQLiteIndex,
    session_id: str,
    window_seconds: int = 300,
) -> dict[str, Any]:
    events = build_session_timeline(index=index, session_id=session_id)
    correlated_events = correlate_session_events(events=events, window_seconds=window_seconds)
    summary = summarize_correlations(correlated_events)
    return {
        "session_id": session_id,
        "window_seconds": window_seconds,
        "summary": summary,
        "events": correlated_events,
    }


def export_session_artifact(
    index: SQLiteIndex,
    session_id: str,
    output_path: Path,
    window_seconds: int = 300,
) -> Path:
    events = build_session_timeline(index=index, session_id=session_id)
    correlation_view = build_correlated_timeline(
        index=index,
        session_id=session_id,
        window_seconds=window_seconds,
    )
    artifact = {
        "generated_at": utc_now_iso(),
        "session_id": session_id,
        "event_count": len(events),
        "sources": sorted({event["source"] for event in events}),
        "events": events,
        "correlation": {
            "window_seconds": window_seconds,
            "summary": correlation_view["summary"],
            "events": correlation_view["events"],
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return output_path
