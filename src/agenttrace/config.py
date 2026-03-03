from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib

CONFIG_VERSION = 1


def _default_sources() -> dict[str, "SourceConfig"]:
    return {
        "claude_code": SourceConfig(enabled=True, path="examples/data/claude_code.ndjson"),
        "codex_cli": SourceConfig(enabled=True, path="examples/data/codex_cli.ndjson"),
        "entra_id": SourceConfig(enabled=True, path="examples/data/entra_id.ndjson"),
        "wso2": SourceConfig(enabled=True, path="examples/data/wso2.ndjson"),
    }


@dataclass(slots=True)
class SourceConfig:
    enabled: bool = True
    path: str = ""


@dataclass(slots=True)
class AppConfig:
    data_dir: str = ".agenttrace/data"
    sqlite_path: str = ".agenttrace/index.db"
    backend_mode: str = "local"
    mapping_version: str = "v1"
    sources: dict[str, SourceConfig] = field(default_factory=_default_sources)


def load_config(config_path: Path) -> AppConfig:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file '{config_path}' does not exist. Run 'agenttrace init' first."
        )
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    sources_blob = data.get("sources", {})
    sources: dict[str, SourceConfig] = {}
    for name, default in _default_sources().items():
        incoming = sources_blob.get(name, {})
        sources[name] = SourceConfig(
            enabled=bool(incoming.get("enabled", default.enabled)),
            path=str(incoming.get("path", default.path)),
        )
    return AppConfig(
        data_dir=str(data.get("data_dir", ".agenttrace/data")),
        sqlite_path=str(data.get("sqlite_path", ".agenttrace/index.db")),
        backend_mode=str(data.get("backend_mode", "local")),
        mapping_version=str(data.get("mapping_version", "v1")),
        sources=sources,
    )


def write_default_config(config_path: Path, force: bool = False) -> None:
    if config_path.exists() and not force:
        raise FileExistsError(
            f"Config file '{config_path}' already exists. Use --force to overwrite."
        )
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(default_config_text(), encoding="utf-8")


def default_config_text() -> str:
    return """# AgentTrace configuration
config_version = 1
data_dir = ".agenttrace/data"
sqlite_path = ".agenttrace/index.db"
backend_mode = "local"
mapping_version = "v1"

[sources.claude_code]
enabled = true
path = "examples/data/claude_code.ndjson"

[sources.codex_cli]
enabled = true
path = "examples/data/codex_cli.ndjson"

[sources.entra_id]
enabled = true
path = "examples/data/entra_id.ndjson"

[sources.wso2]
enabled = true
path = "examples/data/wso2.ndjson"
"""


def resolve_from_config(config_path: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (config_path.parent / path).resolve()
