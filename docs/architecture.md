# AgentTrace Architecture

## Objective

AgentTrace is a post-incident forensic reconstruction layer. It is not a runtime policy engine.

## End-to-End Flow

1. Source adapters ingest agent/runtime and IdP evidence.
2. Records are normalized into a single event envelope.
3. Raw payloads are written to append-only evidence files.
4. Normalized envelopes are written to append-only NDJSON.
5. Provenance and query indexes are maintained in SQLite.
6. Session timelines are replayed, correlated, and exported as artifacts.

## Core Design Decisions

- **Interface:** TUI-first for low-friction operator workflow.
- **Storage:** local hybrid model (files + SQLite), no external dependency for first run.
- **Backend modes:** `local` now, `clickhouse` planned later under one schema contract.
- **Scope boundary:** user/host-level reliability first, enterprise-scale deployment later.

## Event Contract

Every normalized event carries:

- `source`
- `source_event_id`
- `agent_id`
- `identity_id`
- `session_id`
- `event_time`
- `ingest_time`
- `mapping_version`
- `event_type`
- `payload`
- `raw_ref`

## Constraints and Assumptions

- IdP logs may be delayed, incomplete, or throttled.
- Retention windows can prevent full backfill.
- Some Entra paths may require beta APIs in later integration phases.
- Workload identities do not map to human MFA assumptions.

## Correlation Model (Phase 1 Baseline)

Deterministic joins combine:

- `agent_id`
- `identity_id`
- `session_id`
- `correlation_id` when available
- bounded timestamp windows with clock-skew tolerance and deterministic tie-breaks

Evidence tiers (Observed, Reconstructed, Unknown) are added in later phases.
