from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from agenttrace.models import EventEnvelope


class SQLiteIndex:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_event_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    identity_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    ingest_time TEXT NOT NULL,
                    mapping_version TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    raw_ref TEXT NOT NULL,
                    normalized_ref TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(source, source_event_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_session_time ON events(session_id, event_time)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_agent_time ON events(agent_id, event_time)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_identity_time ON events(identity_id, event_time)"
            )
            conn.commit()

    def upsert_event(self, event: EventEnvelope, normalized_ref: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    source, source_event_id, agent_id, identity_id, session_id,
                    event_time, ingest_time, mapping_version, event_type, raw_ref,
                    normalized_ref, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, source_event_id) DO UPDATE SET
                    agent_id = excluded.agent_id,
                    identity_id = excluded.identity_id,
                    session_id = excluded.session_id,
                    event_time = excluded.event_time,
                    ingest_time = excluded.ingest_time,
                    mapping_version = excluded.mapping_version,
                    event_type = excluded.event_type,
                    raw_ref = excluded.raw_ref,
                    normalized_ref = excluded.normalized_ref,
                    payload_json = excluded.payload_json
                """,
                (
                    event.source,
                    event.source_event_id,
                    event.agent_id,
                    event.identity_id,
                    event.session_id,
                    event.event_time,
                    event.ingest_time,
                    event.mapping_version,
                    event.event_type,
                    event.raw_ref,
                    normalized_ref,
                    json.dumps(event.payload, separators=(",", ":")),
                ),
            )
            conn.commit()

    def session_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT source, source_event_id, agent_id, identity_id, session_id,
                       event_time, ingest_time, mapping_version, event_type,
                       raw_ref, normalized_ref, payload_json
                FROM events
                WHERE session_id = ?
                ORDER BY event_time ASC, ingest_time ASC
                """,
                (session_id,),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            events.append(item)
        return events

    def source_health(self, expected_sources: list[str]) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT source, COUNT(*) AS total_events, MAX(ingest_time) AS last_ingest_time
                FROM events
                GROUP BY source
                """
            ).fetchall()
        found = {str(row["source"]): dict(row) for row in rows}
        health: list[dict[str, Any]] = []
        for source in expected_sources:
            row = found.get(source)
            if row is None:
                health.append(
                    {
                        "source": source,
                        "total_events": 0,
                        "last_ingest_time": None,
                    }
                )
                continue
            health.append(
                {
                    "source": source,
                    "total_events": int(row["total_events"]),
                    "last_ingest_time": row["last_ingest_time"],
                }
            )
        return health
