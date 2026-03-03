from pathlib import Path

from rich.console import Console

from agenttrace.tui import run_tui


def test_tui_ingest_correlate_replay_and_export_flow(tmp_path: Path) -> None:
    codex_feed = tmp_path / "codex_cli.ndjson"
    codex_feed.write_text(
        (
            '{"source_event_id":"cx-1","event_time":"2026-03-01T10:00:00Z",'
            '"event_type":"command.run","agent_id":"agent://worker-1",'
            '"identity_id":"spn://entra/spn-001","session_id":"session://incident-1",'
            '"payload":{"command":"terraform plan","correlation_id":"corr-9001"}}\n'
        ),
        encoding="utf-8",
    )
    entra_feed = tmp_path / "entra_id.ndjson"
    entra_feed.write_text(
        (
            '{"id":"signin-1","createdDateTime":"2026-03-01T09:59:50Z",'
            '"category":"SignInLogs","servicePrincipalId":"spn-001",'
            '"session_id":"session://incident-1","correlationId":"corr-9001","resultType":"0"}\n'
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "agenttrace.toml"
    config_path.write_text(
        (
            'config_version = 1\n'
            f'data_dir = "{(tmp_path / "data").as_posix()}"\n'
            f'sqlite_path = "{(tmp_path / "index.db").as_posix()}"\n'
            'backend_mode = "local"\n'
            'mapping_version = "v1"\n'
            "\n"
            "[sources.claude_code]\n"
            "enabled = false\n"
            'path = "unused.ndjson"\n'
            "\n"
            "[sources.codex_cli]\n"
            "enabled = true\n"
            f'path = "{codex_feed.as_posix()}"\n'
            "\n"
            "[sources.entra_id]\n"
            "enabled = true\n"
            f'path = "{entra_feed.as_posix()}"\n'
            "\n"
            "[sources.wso2]\n"
            "enabled = false\n"
            'path = "unused.ndjson"\n'
        ),
        encoding="utf-8",
    )

    responses = iter(
        [
            "1",  # ingest
            "5",  # correlate session
            "session://incident-1",
            "3",  # replay session
            "session://incident-1",
            "4",  # export session
            "session://incident-1",
            "6",  # quit
        ]
    )

    def fake_prompt(*_args, **_kwargs) -> str:
        return next(responses)

    console = Console(record=True, color_system=None, width=200)
    export_dir = tmp_path / "exports"
    run_tui(
        config_path=config_path,
        console=console,
        prompt_fn=fake_prompt,
        export_dir=export_dir,
    )

    output = console.export_text()
    assert "Ingestion Result" in output
    assert "Correlation Summary" in output
    assert "Correlated Timeline" in output
    assert "Timeline - session://incident-1" in output
    assert "session://incident-1" in output

    exported_artifact = export_dir / "session___incident-1.json"
    assert exported_artifact.exists()
