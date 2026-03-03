from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from agenttrace.models import RawRecord


class Connector(Protocol):
    name: str

    def pull(self) -> Iterable[RawRecord]:
        """Return raw records from one source."""
