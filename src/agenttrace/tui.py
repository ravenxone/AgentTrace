from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from agenttrace.pipeline import SourceIngestResult
from agenttrace.runtime import build_runtime
from agenttrace.services import build_session_timeline, export_session_artifact


def run_tui(config_path: Path) -> None:
    runtime = build_runtime(config_path=config_path)
    console = Console()
    console.print("[bold]AgentTrace[/bold] - identity forensics bootstrap")
    while True:
        console.print("\n[1] Ingest  [2] Source Health  [3] Replay Session  [4] Export Session  [5] Quit")
        choice = Prompt.ask("Select action", choices=["1", "2", "3", "4", "5"], default="1")
        if choice == "1":
            results = runtime.pipeline.run()
            _render_ingestion_results(console, results)
        elif choice == "2":
            expected_sources = list(runtime.config.sources.keys())
            status = runtime.index.source_health(expected_sources=expected_sources)
            _render_source_health(console, status)
        elif choice == "3":
            session_id = Prompt.ask("Session ID")
            events = build_session_timeline(runtime.index, session_id=session_id)
            _render_timeline(console, session_id=session_id, events=events)
        elif choice == "4":
            session_id = Prompt.ask("Session ID")
            default_name = _session_file_name(session_id)
            output_path = Path("exports") / default_name
            artifact = export_session_artifact(
                runtime.index, session_id=session_id, output_path=output_path
            )
            console.print(f"Exported artifact: [green]{artifact}[/green]")
        else:
            console.print("Goodbye.")
            break


def _render_ingestion_results(console: Console, results: list[SourceIngestResult]) -> None:
    table = Table(title="Ingestion Result")
    table.add_column("Source")
    table.add_column("Ingested", justify="right")
    table.add_column("Errors")
    for result in results:
        table.add_row(
            result.source,
            str(result.ingested),
            "; ".join(result.errors) if result.errors else "-",
        )
    console.print(table)


def _render_source_health(console: Console, status: list[dict]) -> None:
    table = Table(title="Source Health")
    table.add_column("Source")
    table.add_column("Total Events", justify="right")
    table.add_column("Last Ingest Time")
    for row in status:
        table.add_row(
            str(row["source"]),
            str(row["total_events"]),
            str(row["last_ingest_time"] or "-"),
        )
    console.print(table)


def _render_timeline(console: Console, session_id: str, events: list[dict]) -> None:
    if not events:
        console.print(f"No events found for session [yellow]{session_id}[/yellow].")
        return
    table = Table(title=f"Timeline - {session_id}")
    table.add_column("Event Time")
    table.add_column("Source")
    table.add_column("Type")
    table.add_column("Identity")
    for event in events:
        table.add_row(
            str(event["event_time"]),
            str(event["source"]),
            str(event["event_type"]),
            str(event["identity_id"]),
        )
    console.print(table)


def _session_file_name(session_id: str) -> str:
    safe = session_id.replace("/", "_").replace(":", "_")
    return f"{safe}.json"
