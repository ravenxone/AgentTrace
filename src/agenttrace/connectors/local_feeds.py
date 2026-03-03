from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path

from agenttrace.config import AppConfig, resolve_from_config
from agenttrace.models import RawRecord, utc_now_iso


class LocalNDJSONConnector:
    """Reads local NDJSON files as source adapters for MVP ingestion."""

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path

    def pull(self) -> Iterable[RawRecord]:
        if not self.path.exists():
            return []
        records: list[RawRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                payload_line = line.strip()
                if not payload_line:
                    continue
                parsed = json.loads(payload_line)
                records.append(
                    RawRecord(
                        source=self.name,
                        source_event_id=str(
                            parsed.get("source_event_id")
                            or parsed.get("id")
                            or f"{self.name}-{line_no}"
                        ),
                        event_time=str(parsed.get("event_time") or utc_now_iso()),
                        event_type=str(parsed.get("event_type") or "unknown"),
                        agent_id=str(parsed.get("agent_id") or "agent://unknown"),
                        identity_id=str(parsed.get("identity_id") or "identity://unknown"),
                        session_id=str(parsed.get("session_id") or "session://unknown"),
                        payload=dict(parsed.get("payload") or {}),
                        raw_payload=parsed,
                    )
                )
        return records


def build_connectors(config: AppConfig, config_path: Path) -> list[LocalNDJSONConnector]:
    connectors: list[LocalNDJSONConnector] = []
    for source_name, source_cfg in config.sources.items():
        if not source_cfg.enabled:
            continue
        connectors.append(
            LocalNDJSONConnector(
                name=source_name,
                path=resolve_from_config(config_path, source_cfg.path),
            )
        )
    return connectors
