# Source Connectors

## Adapter Strategy

Phase 0/1 prioritizes stable ingestion contracts. Connectors ingest NDJSON feeds and normalize them into AgentTrace envelopes.

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

## Entra ID Normalization Notes

The `entra_id` connector also accepts Graph-style fields such as:

- `createdDateTime` / `activityDateTime`
- `correlationId`
- `servicePrincipalId`
- `activityDisplayName`
- `resultType`

These are mapped into AgentTrace provenance fields and deterministic correlation hints (`correlation_id` in payload).

## Integration Path (Phase 1+)

- Replace file adapters with API-backed collectors.
- Preserve same normalized envelope to avoid downstream breakage.
- Add collection watermarking and backoff-aware retries.
- Introduce source-specific provenance tags and mapping versions.
