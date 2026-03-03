from pathlib import Path

from agenttrace.connectors.local_feeds import LocalNDJSONConnector
from agenttrace.pipeline import IngestionPipeline
from agenttrace.storage.file_store import EvidenceStore
from agenttrace.storage.sqlite_index import SQLiteIndex


def test_pipeline_ingests_and_indexes_records(tmp_path: Path) -> None:
    feed = tmp_path / "claude_code.ndjson"
    feed.write_text(
        (
            '{"id":"evt-1","event_time":"2026-03-01T10:00:00Z","event_type":"tool.call",'
            '"agent_id":"agent://a1","identity_id":"spn://entra/app-1",'
            '"session_id":"session://s1","payload":{"tool":"az"}}\n'
        ),
        encoding="utf-8",
    )

    connectors = [LocalNDJSONConnector(name="claude_code", path=feed)]
    store = EvidenceStore(data_dir=tmp_path / "data")
    index = SQLiteIndex(db_path=tmp_path / "index.db")
    pipeline = IngestionPipeline(
        connectors=connectors,
        store=store,
        index=index,
        mapping_version="v-test",
    )

    results = pipeline.run()
    assert len(results) == 1
    assert results[0].source == "claude_code"
    assert results[0].ingested == 1
    assert not results[0].errors

    timeline = index.session_events("session://s1")
    assert len(timeline) == 1
    assert timeline[0]["source_event_id"] == "evt-1"
    assert timeline[0]["mapping_version"] == "v-test"
