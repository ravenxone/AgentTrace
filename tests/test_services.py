import json
from pathlib import Path

from agenttrace.connectors.local_feeds import LocalNDJSONConnector
from agenttrace.pipeline import IngestionPipeline
from agenttrace.services import export_session_artifact
from agenttrace.storage.file_store import EvidenceStore
from agenttrace.storage.sqlite_index import SQLiteIndex


def test_export_session_artifact_contains_events(tmp_path: Path) -> None:
    feed = tmp_path / "codex_cli.ndjson"
    feed.write_text(
        (
            '{"id":"evt-1","event_time":"2026-03-01T10:00:00Z","event_type":"command.run",'
            '"agent_id":"agent://a1","identity_id":"spn://entra/app-1",'
            '"session_id":"session://s2","payload":{"command":"terraform plan"}}\n'
            '{"id":"evt-2","event_time":"2026-03-01T10:01:00Z","event_type":"command.run",'
            '"agent_id":"agent://a1","identity_id":"spn://entra/app-1",'
            '"session_id":"session://s2","payload":{"command":"terraform apply"}}\n'
        ),
        encoding="utf-8",
    )

    connectors = [LocalNDJSONConnector(name="codex_cli", path=feed)]
    store = EvidenceStore(data_dir=tmp_path / "data")
    index = SQLiteIndex(db_path=tmp_path / "index.db")
    pipeline = IngestionPipeline(
        connectors=connectors,
        store=store,
        index=index,
        mapping_version="v-test",
    )
    pipeline.run()

    output = tmp_path / "exports" / "session_s2.json"
    export_session_artifact(index=index, session_id="session://s2", output_path=output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["session_id"] == "session://s2"
    assert payload["event_count"] == 2
    assert payload["sources"] == ["codex_cli"]
    assert payload["correlation"]["window_seconds"] == 300
    assert payload["correlation"]["summary"]["runtime_actions"] == 2
