# AgentTrace Roadmap

## Phase 0 - Bootstrap MVP (Implemented)

- TUI-first operator experience.
- Source adapters for `Claude Code`, `Codex CLI`, `Entra ID`, and `WSO2`.
- Normalize all records into one envelope schema.
- Persist raw and normalized evidence locally.
- Maintain SQLite index for replay and export workflows.

### Phase 0 Success Metrics

- Source coverage (% configured sources ingested successfully).
- Ingestion reliability (runs without data loss on local replay).
- Replayability from local evidence files + index.

## Phase 1 - Correlation Baseline (Implemented)

- Deterministic joins across identity and runtime evidence.
- Join keys: `agent_id`, `identity_id`, `session_id`, and `correlation_id` when present.
- Bounded timestamp windows with deterministic tie-breaking.
- Timeline reconstruction quality checks on synthetic scenarios.
- Structured session report export with confidence indicators.

### Phase 1 Success Metrics

- Median time-to-reconstruct vs manual baseline.
- % high-risk actions with high-confidence identity attribution.

## Phase 2 - Expansion

- Optional ClickHouse backend mode for high-volume analysis.
- Web UI for richer investigation workflows.
- Evidence tiering and expanded heuristic modules.

### Phase 2 Success Metrics

- % session events with explicit evidence class.
- Correlation coverage improvement across additional event types.
