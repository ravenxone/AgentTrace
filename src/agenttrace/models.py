from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class RawRecord:
    source: str
    source_event_id: str
    event_time: str
    event_type: str
    agent_id: str
    identity_id: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventEnvelope:
    source: str
    source_event_id: str
    agent_id: str
    identity_id: str
    session_id: str
    event_time: str
    ingest_time: str
    mapping_version: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    raw_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
