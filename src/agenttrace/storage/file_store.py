from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from agenttrace.models import EventEnvelope, RawRecord


class EvidenceStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.raw_root = self.data_dir / "raw"
        self.normalized_root = self.data_dir / "normalized"
        self.snapshot_root = self.data_dir / "snapshots"
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self.normalized_root.mkdir(parents=True, exist_ok=True)
        self.snapshot_root.mkdir(parents=True, exist_ok=True)

    def append_raw(self, record: RawRecord) -> str:
        file_path = self._daily_source_path(record.source)
        body = {
            "ingest_time": datetime.now(tz=timezone.utc).isoformat(),
            "source": record.source,
            "source_event_id": record.source_event_id,
            "raw_payload": record.raw_payload,
        }
        self._append_json_line(file_path, body)
        return str(file_path)

    def append_normalized(self, event: EventEnvelope) -> str:
        file_path = self._daily_normalized_path()
        self._append_json_line(file_path, event.to_dict())
        return str(file_path)

    def write_snapshot(self, name: str, payload: dict[str, Any]) -> Path:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.snapshot_root / f"{name}_{timestamp}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def _daily_source_path(self, source: str) -> Path:
        stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        source_dir = self.raw_root / source
        source_dir.mkdir(parents=True, exist_ok=True)
        return source_dir / f"{stamp}.ndjson"

    def _daily_normalized_path(self) -> Path:
        stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        return self.normalized_root / f"{stamp}.ndjson"

    @staticmethod
    def _append_json_line(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, separators=(",", ":")))
            handle.write("\n")
