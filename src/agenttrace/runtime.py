from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agenttrace.config import AppConfig, load_config, resolve_from_config
from agenttrace.connectors.local_feeds import build_connectors
from agenttrace.pipeline import IngestionPipeline
from agenttrace.storage.file_store import EvidenceStore
from agenttrace.storage.sqlite_index import SQLiteIndex


@dataclass(slots=True)
class RuntimeContext:
    config_path: Path
    config: AppConfig
    connectors: list
    store: EvidenceStore
    index: SQLiteIndex
    pipeline: IngestionPipeline


def build_runtime(config_path: Path) -> RuntimeContext:
    config = load_config(config_path)
    if config.backend_mode != "local":
        raise ValueError(
            f"Unsupported backend_mode='{config.backend_mode}'. "
            "Only 'local' is available in this MVP."
        )
    data_dir = resolve_from_config(config_path, config.data_dir)
    sqlite_path = resolve_from_config(config_path, config.sqlite_path)
    connectors = build_connectors(config=config, config_path=config_path)
    store = EvidenceStore(data_dir=data_dir)
    index = SQLiteIndex(db_path=sqlite_path)
    pipeline = IngestionPipeline(
        connectors=connectors,
        store=store,
        index=index,
        mapping_version=config.mapping_version,
    )
    return RuntimeContext(
        config_path=config_path,
        config=config,
        connectors=connectors,
        store=store,
        index=index,
        pipeline=pipeline,
    )
