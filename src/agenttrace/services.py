from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agenttrace.models import utc_now_iso
from agenttrace.storage.sqlite_index import SQLiteIndex


def build_session_timeline(index: SQLiteIndex, session_id: str) -> list[dict[str, Any]]:
    return index.session_events(session_id=session_id)


def export_session_artifact(
    index: SQLiteIndex,
    session_id: str,
    output_path: Path,
) -> Path:
    events = build_session_timeline(index=index, session_id=session_id)
    artifact = {
        "generated_at": utc_now_iso(),
        "session_id": session_id,
        "event_count": len(events),
        "sources": sorted({event["source"] for event in events}),
        "events": events,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return output_path
