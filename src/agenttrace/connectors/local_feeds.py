from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path

from agenttrace.config import AppConfig, resolve_from_config
from agenttrace.connectors.base import Connector
from agenttrace.connectors.entra_id import EntraIDConnector
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
                payload = dict(parsed.get("payload") or {})
                correlation_id = str(
                    parsed.get("correlation_id")
                    or parsed.get("correlationId")
                    or parsed.get("requestId")
                    or ""
                )
                if correlation_id and "correlation_id" not in payload:
                    payload["correlation_id"] = correlation_id
                session_id = str(parsed.get("session_id") or "session://unknown")
                if session_id == "session://unknown" and correlation_id:
                    session_id = f"session://trace/{correlation_id}"
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
                        session_id=session_id,
                        payload=payload,
                        raw_payload=parsed,
                    )
                )
        return records


def build_connectors(config: AppConfig, config_path: Path) -> list[Connector]:
    connectors: list[Connector] = []
    for source_name, source_cfg in config.sources.items():
        if not source_cfg.enabled:
            continue
        source_path = resolve_from_config(config_path, source_cfg.path)
        if source_name == "entra_id":
            connectors.append(
                EntraIDConnector(
                    name=source_name,
                    path=source_path,
                )
            )
            continue
        connectors.append(
            LocalNDJSONConnector(
                name=source_name,
                path=source_path,
            )
        )
    return connectors
