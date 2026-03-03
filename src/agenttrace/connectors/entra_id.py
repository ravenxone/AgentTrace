from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import re

from agenttrace.models import RawRecord, utc_now_iso


class EntraIDConnector:
    """Normalize Entra sign-in and audit feeds into AgentTrace records."""

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path

    def pull(self) -> Iterable[RawRecord]:
        if not self.path.exists():
            return []
        records: list[RawRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                payload_line = line.strip()
                if not payload_line:
                    continue
                parsed = json.loads(payload_line)
                correlation_id = _extract_correlation_id(parsed)
                records.append(
                    RawRecord(
                        source=self.name,
                        source_event_id=str(
                            parsed.get("source_event_id")
                            or parsed.get("id")
                            or f"{self.name}-{line_no}"
                        ),
                        event_time=_extract_event_time(parsed),
                        event_type=_extract_event_type(parsed),
                        agent_id=_extract_agent_id(parsed),
                        identity_id=_extract_identity_id(parsed),
                        session_id=_extract_session_id(parsed, correlation_id=correlation_id),
                        payload=_extract_payload(parsed, correlation_id=correlation_id),
                        raw_payload=parsed,
                    )
                )
        return records


def _extract_event_time(event: dict) -> str:
    return str(
        event.get("event_time")
        or event.get("createdDateTime")
        or event.get("activityDateTime")
        or utc_now_iso()
    )


def _extract_event_type(event: dict) -> str:
    explicit = event.get("event_type")
    if explicit:
        return str(explicit)

    category = str(event.get("category") or "").lower()
    if "signin" in category or "resultType" in event:
        result = str(event.get("resultType") or "").lower()
        if result in {"0", "success", "succeeded"}:
            return "signin.success"
        if result:
            return "signin.failure"
        return "signin.unknown"

    activity = event.get("activityDisplayName")
    if activity:
        return f"audit.{_slug(str(activity))}"

    if category:
        return f"audit.{_slug(category)}"
    return "unknown"


def _extract_agent_id(event: dict) -> str:
    explicit = event.get("agent_id")
    if explicit:
        return str(explicit)
    principal = (
        event.get("servicePrincipalId")
        or event.get("servicePrincipalObjectId")
        or event.get("principalId")
    )
    if principal:
        return f"agent://workload/{principal}"
    app_id = event.get("appId")
    if app_id:
        return f"agent://app/{app_id}"
    return "agent://unknown"


def _extract_identity_id(event: dict) -> str:
    explicit = event.get("identity_id")
    if explicit:
        return str(explicit)
    principal = (
        event.get("servicePrincipalId")
        or event.get("servicePrincipalObjectId")
        or event.get("principalId")
    )
    if principal:
        return f"spn://entra/{principal}"
    app_id = event.get("appId")
    if app_id:
        return f"spn://entra/app:{app_id}"
    upn = event.get("userPrincipalName")
    if upn:
        return f"user://entra/{upn}"
    return "identity://unknown"


def _extract_correlation_id(event: dict) -> str:
    return str(
        event.get("correlation_id")
        or event.get("correlationId")
        or event.get("requestId")
        or ""
    )


def _extract_session_id(event: dict, correlation_id: str) -> str:
    explicit = event.get("session_id")
    if explicit:
        return str(explicit)
    if correlation_id:
        return f"session://entra/{correlation_id}"
    return "session://unknown"


def _extract_payload(event: dict, correlation_id: str) -> dict:
    payload = dict(event.get("payload") or {})
    if correlation_id and "correlation_id" not in payload:
        payload["correlation_id"] = correlation_id
    for key in (
        "appId",
        "appDisplayName",
        "ipAddress",
        "resultType",
        "resultDescription",
        "category",
        "activityDisplayName",
    ):
        if key in event and key not in payload:
            payload[key] = event[key]
    return payload


def _slug(value: str) -> str:
    normalized = value.strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
