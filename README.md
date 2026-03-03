# AgentTrace

AgentTrace is an open-source, read-only forensic correlation project for IAM investigations.

## Problem

Enterprise teams can usually see:
Agent/runtime execution telemetry in one system.Identity authentication and authorization evidence in separate IdP systems. During an incident, they rarely have a single, defensible timeline that links both. This slows investigation and weakens confidence in identity recovery decisions. AgentTrace is built to solve this problem. 

AgentTrace creates a local, deterministic evidence trail that can be replayed and expanded into deeper correlation phases.


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

## Explicit Non-Goals

- Runtime enforcement or blocking.
- Automated remediation.
- Full policy engine in MVP.
- Broad multi-cloud identity support in MVP.
