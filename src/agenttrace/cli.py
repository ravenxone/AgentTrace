from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agenttrace.config import write_default_config
from agenttrace.runtime import build_runtime
from agenttrace.services import build_session_timeline, export_session_artifact
from agenttrace.tui import run_tui

app = typer.Typer(help="AgentTrace forensic ingestion and replay toolkit.")
console = Console()


@app.command()
def init(
    config: Path = typer.Option(Path("agenttrace.toml"), help="Path to config file."),
    force: bool = typer.Option(False, help="Overwrite config if it already exists."),
) -> None:
    """Create a default local AgentTrace configuration."""
    write_default_config(config_path=config, force=force)
    console.print(f"Wrote config: [green]{config}[/green]")


@app.command()
def ingest(
    config: Path = typer.Option(Path("agenttrace.toml"), help="Path to config file."),
) -> None:
    """Ingest evidence from configured sources into local storage."""
    runtime = build_runtime(config_path=config)
    results = runtime.pipeline.run()
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


@app.command()
def status(
    config: Path = typer.Option(Path("agenttrace.toml"), help="Path to config file."),
) -> None:
    """Show ingestion health per source."""
    runtime = build_runtime(config_path=config)
    health = runtime.index.source_health(expected_sources=list(runtime.config.sources.keys()))
    table = Table(title="Source Health")
    table.add_column("Source")
    table.add_column("Total Events", justify="right")
    table.add_column("Last Ingest Time")
    for row in health:
        table.add_row(
            str(row["source"]),
            str(row["total_events"]),
            str(row["last_ingest_time"] or "-"),
        )
    console.print(table)


@app.command()
def replay(
    session_id: str = typer.Argument(..., help="Session identifier to replay."),
    config: Path = typer.Option(Path("agenttrace.toml"), help="Path to config file."),
) -> None:
    """Render a timeline for one session."""
    runtime = build_runtime(config_path=config)
    events = build_session_timeline(index=runtime.index, session_id=session_id)
    if not events:
        console.print(f"No events found for session [yellow]{session_id}[/yellow].")
        raise typer.Exit(code=1)
    table = Table(title=f"Timeline - {session_id}")
    table.add_column("Event Time")
    table.add_column("Source")
    table.add_column("Type")
    table.add_column("Agent")
    table.add_column("Identity")
    for event in events:
        table.add_row(
            str(event["event_time"]),
            str(event["source"]),
            str(event["event_type"]),
            str(event["agent_id"]),
            str(event["identity_id"]),
        )
    console.print(table)


@app.command()
def export(
    session_id: str = typer.Argument(..., help="Session identifier to export."),
    output: Path = typer.Option(
        Path("exports/session_artifact.json"),
        help="Path for JSON artifact output.",
    ),
    config: Path = typer.Option(Path("agenttrace.toml"), help="Path to config file."),
) -> None:
    """Export a JSON investigation artifact for one session."""
    runtime = build_runtime(config_path=config)
    path = export_session_artifact(
        index=runtime.index,
        session_id=session_id,
        output_path=output,
    )
    console.print(f"Wrote artifact: [green]{path}[/green]")


@app.command()
def tui(
    config: Path = typer.Option(Path("agenttrace.toml"), help="Path to config file."),
) -> None:
    """Launch the terminal-first investigation interface."""
    run_tui(config_path=config)
