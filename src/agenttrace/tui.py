from __future__ import annotations

from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from agenttrace.pipeline import SourceIngestResult
from agenttrace.runtime import build_runtime
from agenttrace.services import (
    build_correlated_timeline,
    build_session_timeline,
    export_session_artifact,
)


def run_tui(
    config_path: Path,
    console: Console | None = None,
    prompt_fn: Callable[..., str] | None = None,
    export_dir: Path | None = None,
) -> None:
    runtime = build_runtime(config_path=config_path)
    console = console or Console()
    prompt_fn = prompt_fn or Prompt.ask
    export_dir = export_dir or Path("exports")
    console.print("[bold]AgentTrace[/bold] - identity forensics bootstrap")
    while True:
        console.print(
            "\n[1] Ingest  [2] Source Health  [3] Replay Session  "
            "[4] Export Session  [5] Correlate Session  [6] Quit"
        )
        choice = prompt_fn("Select action", choices=["1", "2", "3", "4", "5", "6"], default="1")
        if choice == "1":
            results = runtime.pipeline.run()
            _render_ingestion_results(console, results)
        elif choice == "2":
            expected_sources = list(runtime.config.sources.keys())
            status = runtime.index.source_health(expected_sources=expected_sources)
            _render_source_health(console, status)
        elif choice == "3":
            session_id = prompt_fn("Session ID")
            events = build_session_timeline(runtime.index, session_id=session_id)
            _render_timeline(console, session_id=session_id, events=events)
        elif choice == "4":
            session_id = prompt_fn("Session ID")
            default_name = _session_file_name(session_id)
            output_path = export_dir / default_name
            artifact = export_session_artifact(
                runtime.index, session_id=session_id, output_path=output_path
            )
            console.print(f"Exported artifact: [green]{artifact}[/green]")
        elif choice == "5":
            session_id = prompt_fn("Session ID")
            correlation_view = build_correlated_timeline(runtime.index, session_id=session_id)
            _render_correlated_timeline(console, session_id=session_id, correlation_view=correlation_view)
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


def _render_correlated_timeline(
    console: Console,
    session_id: str,
    correlation_view: dict,
) -> None:
    events = correlation_view.get("events") or []
    if not events:
        console.print(f"No events found for session [yellow]{session_id}[/yellow].")
        return
    summary = correlation_view.get("summary") or {}
    summary_table = Table(title=f"Correlation Summary - {session_id}")
    summary_table.add_column("Metric")
    summary_table.add_column("Value", justify="right")
    for key in (
        "runtime_actions",
        "matched_actions",
        "unmatched_actions",
        "high_confidence",
        "medium_confidence",
        "low_confidence",
        "unknown_confidence",
    ):
        summary_table.add_row(key, str(summary.get(key, 0)))
    console.print(summary_table)

    table = Table(title=f"Correlated Timeline - {session_id}")
    table.add_column("Runtime Event")
    table.add_column("Matched Identity Event")
    table.add_column("Confidence")
    table.add_column("Reasons")
    for event in events:
        if event.get("role") != "runtime_action":
            continue
        correlation = event.get("correlation") or {}
        matched_event = correlation.get("matched_event") or {}
        table.add_row(
            str(event.get("source_event_id")),
            str(matched_event.get("source_event_id") or "-"),
            str(correlation.get("confidence") or "unknown"),
            ",".join(correlation.get("reason_codes") or []),
        )
    console.print(table)


def _session_file_name(session_id: str) -> str:
    safe = session_id.replace("/", "_").replace(":", "_")
    return f"{safe}.json"
