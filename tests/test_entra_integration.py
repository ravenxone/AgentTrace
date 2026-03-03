from pathlib import Path

from agenttrace.config import AppConfig, SourceConfig
from agenttrace.connectors.entra_id import EntraIDConnector
from agenttrace.connectors.local_feeds import LocalNDJSONConnector, build_connectors


def test_entra_connector_normalizes_signin_and_audit_records(tmp_path: Path) -> None:
    feed = tmp_path / "entra_id.ndjson"
    feed.write_text(
        (
            '{"id":"signin-1","createdDateTime":"2026-03-01T09:59:45Z",'
            '"category":"SignInLogs","servicePrincipalId":"spn-001",'
            '"correlationId":"corr-9001","resultType":"0","appDisplayName":"Agent Worker"}\n'
            '{"id":"audit-1","activityDateTime":"2026-03-01T10:00:10Z",'
            '"category":"AuditLogs","activityDisplayName":"Add app role assignment to service principal",'
            '"servicePrincipalId":"spn-001","correlationId":"corr-9001"}\n'
        ),
        encoding="utf-8",
    )

    connector = EntraIDConnector(name="entra_id", path=feed)
    records = list(connector.pull())

    assert len(records) == 2
    assert records[0].source_event_id == "signin-1"
    assert records[0].event_type == "signin.success"
    assert records[0].agent_id == "agent://workload/spn-001"
    assert records[0].identity_id == "spn://entra/spn-001"
    assert records[0].session_id == "session://entra/corr-9001"
    assert records[0].payload["correlation_id"] == "corr-9001"

    assert records[1].source_event_id == "audit-1"
    assert records[1].event_type == "audit.add_app_role_assignment_to_service_principal"
    assert records[1].payload["correlation_id"] == "corr-9001"


def test_build_connectors_uses_entra_connector_for_entra_source(tmp_path: Path) -> None:
    config_path = tmp_path / "agenttrace.toml"
    config_path.write_text("# placeholder", encoding="utf-8")

    config = AppConfig(
        data_dir=str(tmp_path / "data"),
        sqlite_path=str(tmp_path / "index.db"),
        backend_mode="local",
        mapping_version="v1",
        sources={
            "entra_id": SourceConfig(enabled=True, path="entra.ndjson"),
            "codex_cli": SourceConfig(enabled=True, path="codex.ndjson"),
        },
    )
    (tmp_path / "entra.ndjson").write_text("", encoding="utf-8")
    (tmp_path / "codex.ndjson").write_text("", encoding="utf-8")

    connectors = build_connectors(config=config, config_path=config_path)
    assert len(connectors) == 2
    assert isinstance(connectors[0], EntraIDConnector)
    assert isinstance(connectors[1], LocalNDJSONConnector)
