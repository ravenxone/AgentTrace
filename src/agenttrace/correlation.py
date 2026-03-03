from __future__ import annotations

from datetime import datetime
from typing import Any

DEFAULT_RUNTIME_SOURCES = {"claude_code", "codex_cli"}
DEFAULT_IDENTITY_SOURCES = {"entra_id", "wso2"}


def correlate_session_events(
    events: list[dict[str, Any]],
    window_seconds: int = 300,
    runtime_sources: set[str] | None = None,
    identity_sources: set[str] | None = None,
) -> list[dict[str, Any]]:
    runtime_sources = runtime_sources or DEFAULT_RUNTIME_SOURCES
    identity_sources = identity_sources or DEFAULT_IDENTITY_SOURCES

    ordered = sorted(events, key=lambda event: (_safe_time(event["event_time"]), event["ingest_time"]))
    identity_events = [event for event in ordered if event.get("source") in identity_sources]

    correlated: list[dict[str, Any]] = []
    for event in ordered:
        source = str(event.get("source"))
        if source in identity_sources:
            correlated.append(
                {
                    **event,
                    "role": "identity_evidence",
                }
            )
            continue

        if source not in runtime_sources:
            correlated.append(
                {
                    **event,
                    "role": "other",
                }
            )
            continue

        match = _best_identity_match(
            runtime_event=event,
            identity_events=identity_events,
            window_seconds=window_seconds,
        )
        if match is None:
            correlated.append(
                {
                    **event,
                    "role": "runtime_action",
                    "correlation": {
                        "status": "unmatched",
                        "confidence": "unknown",
                        "score": 0,
                        "time_delta_seconds": None,
                        "reason_codes": ["no_identity_evidence_in_window"],
                        "matched_event": None,
                    },
                }
            )
            continue

        correlated.append(
            {
                **event,
                "role": "runtime_action",
                "correlation": {
                    "status": "matched",
                    "confidence": _confidence_for_score(match["score"]),
                    "score": match["score"],
                    "time_delta_seconds": match["time_delta_seconds"],
                    "reason_codes": match["reason_codes"],
                    "matched_event": {
                        "source": match["event"]["source"],
                        "source_event_id": match["event"]["source_event_id"],
                        "event_time": match["event"]["event_time"],
                        "event_type": match["event"]["event_type"],
                        "identity_id": match["event"]["identity_id"],
                    },
                },
            }
        )
    return correlated


def summarize_correlations(correlated_events: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "runtime_actions": 0,
        "matched_actions": 0,
        "unmatched_actions": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
        "unknown_confidence": 0,
    }
    for event in correlated_events:
        if event.get("role") != "runtime_action":
            continue
        summary["runtime_actions"] += 1
        correlation = event.get("correlation") or {}
        confidence = str(correlation.get("confidence") or "unknown")
        if str(correlation.get("status")) == "matched":
            summary["matched_actions"] += 1
        else:
            summary["unmatched_actions"] += 1
        if confidence == "high":
            summary["high_confidence"] += 1
        elif confidence == "medium":
            summary["medium_confidence"] += 1
        elif confidence == "low":
            summary["low_confidence"] += 1
        else:
            summary["unknown_confidence"] += 1
    return summary


def _best_identity_match(
    runtime_event: dict[str, Any],
    identity_events: list[dict[str, Any]],
    window_seconds: int,
) -> dict[str, Any] | None:
    runtime_time = _safe_time(str(runtime_event.get("event_time", "")))
    if runtime_time is None:
        return None

    best: dict[str, Any] | None = None
    for identity_event in identity_events:
        identity_time = _safe_time(str(identity_event.get("event_time", "")))
        if identity_time is None:
            continue

        time_delta_seconds = abs((runtime_time - identity_time).total_seconds())
        if time_delta_seconds > window_seconds:
            continue

        score, reasons = _score_match(runtime_event=runtime_event, identity_event=identity_event)
        if score == 0:
            continue

        candidate = {
            "event": identity_event,
            "score": score,
            "reason_codes": reasons,
            "time_delta_seconds": int(time_delta_seconds),
        }
        if best is None:
            best = candidate
            continue

        # Deterministic tie-breaker: higher score, then lower time delta.
        if score > best["score"] or (
            score == best["score"] and time_delta_seconds < best["time_delta_seconds"]
        ):
            best = candidate
    return best


def _score_match(runtime_event: dict[str, Any], identity_event: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    runtime_corr = _extract_correlation_id(runtime_event)
    identity_corr = _extract_correlation_id(identity_event)
    if runtime_corr and identity_corr and runtime_corr == identity_corr:
        score += 5
        reasons.append("correlation_id")

    runtime_session = str(runtime_event.get("session_id") or "")
    identity_session = str(identity_event.get("session_id") or "")
    if runtime_session and identity_session and runtime_session == identity_session:
        score += 2
        reasons.append("session_id")

    runtime_identity = str(runtime_event.get("identity_id") or "")
    identity_identity = str(identity_event.get("identity_id") or "")
    if runtime_identity and identity_identity and runtime_identity == identity_identity:
        score += 2
        reasons.append("identity_id")

    runtime_agent = str(runtime_event.get("agent_id") or "")
    identity_agent = str(identity_event.get("agent_id") or "")
    if runtime_agent and identity_agent and runtime_agent == identity_agent:
        score += 1
        reasons.append("agent_id")

    return score, reasons


def _confidence_for_score(score: int) -> str:
    if score >= 8:
        return "high"
    if score >= 5:
        return "medium"
    if score > 0:
        return "low"
    return "unknown"


def _extract_correlation_id(event: dict[str, Any]) -> str:
    payload = event.get("payload")
    if isinstance(payload, dict):
        if payload.get("correlation_id"):
            return str(payload["correlation_id"])
        if payload.get("correlationId"):
            return str(payload["correlationId"])
        if payload.get("request_id"):
            return str(payload["request_id"])
    return str(
        event.get("correlation_id")
        or event.get("correlationId")
        or event.get("request_id")
        or ""
    )


def _safe_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
