from __future__ import annotations

from dataclasses import dataclass, field

from agenttrace.connectors.base import Connector
from agenttrace.models import EventEnvelope, RawRecord, utc_now_iso
from agenttrace.storage.file_store import EvidenceStore
from agenttrace.storage.sqlite_index import SQLiteIndex


@dataclass(slots=True)
class SourceIngestResult:
    source: str
    ingested: int = 0
    errors: list[str] = field(default_factory=list)


class IngestionPipeline:
    def __init__(
        self,
        connectors: list[Connector],
        store: EvidenceStore,
        index: SQLiteIndex,
        mapping_version: str,
    ):
        self.connectors = connectors
        self.store = store
        self.index = index
        self.mapping_version = mapping_version

    def run(self) -> list[SourceIngestResult]:
        results: list[SourceIngestResult] = []
        for connector in self.connectors:
            result = SourceIngestResult(source=connector.name)
            try:
                for record in connector.pull():
                    event = self._normalize_record(record)
                    normalized_ref = self.store.append_normalized(event)
                    self.index.upsert_event(event, normalized_ref=normalized_ref)
                    result.ingested += 1
            except Exception as exc:  # noqa: BLE001 - keep source-level failures visible.
                result.errors.append(str(exc))
            results.append(result)
        return results

    def _normalize_record(self, record: RawRecord) -> EventEnvelope:
        raw_ref = self.store.append_raw(record)
        return EventEnvelope(
            source=record.source,
            source_event_id=record.source_event_id,
            agent_id=record.agent_id,
            identity_id=record.identity_id,
            session_id=record.session_id,
            event_time=record.event_time,
            ingest_time=utc_now_iso(),
            mapping_version=self.mapping_version,
            event_type=record.event_type,
            payload=record.payload,
            raw_ref=raw_ref,
        )
