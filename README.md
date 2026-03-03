# AgentTrace

AgentTrace is an open-source agent identity & forensics library that unifies AI agent execution data with enterprise identity systems (e.g. Microsoft Entra ID, WSO2, code/CLI agents) into a single evidence layer for audit and post-incident reconstruction.

## Problem

**"What did this agent do, which identity did it use, and was that identity state appropriate at that moment?"**

The current implementation includes **Phase 0 + Phase 1 baseline**:

- ingestion-first evidence collection
- deterministic session correlation on `agent_id`, `identity_id`, `session_id`, and `correlation_id` (when present), bounded by timestamp windows
- timeline replay and correlation-aware export

Enterprise teams can usually see agent/runtime execution telemetry in one system and identity authentication/authorization evidence in separate IdP systems. During an incident, they rarely have a single, defensible timeline that links both. This slows investigation and weakens confidence in identity recovery decisions.

AgentTrace creates a local, deterministic evidence trail that can be replayed and expanded into deeper correlation phases.

## Current Capabilities (Phase 0 + Phase 1 Baseline)

- TUI-first workflow for ingestion and investigation.
- Source adapters for:
  - `Claude Code`
  - `Codex CLI`
  - `Microsoft Entra ID` (adapter feed for MVP)
  - `WSO2` (adapter feed for MVP)
- Unified normalized event envelope with provenance metadata.
- Hybrid local storage:
  - append-only NDJSON raw evidence
  - append-only NDJSON normalized events
  - SQLite index for fast lookup and replay
- Session timeline replay and JSON artifact export.
- Deterministic correlation summaries and correlated timeline views.

## Quick Start

```bash
./scripts/bootstrap.sh
```

This command:

1. Creates a virtual environment.
2. Installs AgentTrace.
3. Creates `agenttrace.toml` if missing.
4. Launches the TUI.

## CLI Usage

```bash
agenttrace init --config agenttrace.toml
agenttrace ingest --config agenttrace.toml
agenttrace status --config agenttrace.toml
agenttrace replay "session://incident-1042" --config agenttrace.toml
agenttrace correlate "session://incident-1042" --window-seconds 300 --config agenttrace.toml
agenttrace export "session://incident-1042" --output exports/incident-1042.json --config agenttrace.toml
agenttrace tui --config agenttrace.toml
```

## Provenance Fields (Required)

Each normalized event includes:

- `source`
- `source_event_id`
- `agent_id`
- `identity_id`
- `session_id`
- `event_time`
- `ingest_time`
- `mapping_version`

Raw source payloads are preserved immutably in append-only evidence files.

## Project Layout

```text
src/agenttrace/
  cli.py
  tui.py
  config.py
  connectors/
  storage/
  pipeline.py
  services.py
examples/data/
docs/
scripts/bootstrap.sh
```

## Phased Roadmap

- **Phase 0 (implemented):** ingestion reliability, local replay, provenance-safe evidence retention.
- **Phase 1 baseline (implemented):** deterministic timeline reconstruction and bounded-window correlation.
- **Phase 2:** evidence tiering, expanded heuristics, optional web UI, and optional ClickHouse backend mode.
## Explicit Non-Goals

- Runtime enforcement or blocking.
- Automated remediation.
- Full policy engine in MVP.
- Broad multi-cloud identity support in MVP.
