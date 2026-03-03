# Source Connectors

## MVP Adapter Strategy

Phase 0 prioritizes stable ingestion contracts. Connectors currently ingest NDJSON feeds and normalize them into AgentTrace envelopes.

Supported source names:

- `claude_code`
- `codex_cli`
- `entra_id`
- `wso2`

## Input Schema (Minimum)

Each source line may include:

- `source_event_id`
- `event_time`
- `event_type`
- `agent_id`
- `identity_id`
- `session_id`
- `payload`

Missing fields are backfilled with safe defaults in MVP.

## Integration Path (Phase 1+)

- Replace file adapters with API-backed collectors.
- Preserve same normalized envelope to avoid downstream breakage.
- Add collection watermarking and backoff-aware retries.
- Introduce source-specific provenance tags and mapping versions.
