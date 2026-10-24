"""Future native pen-record writer; no encoding implementation yet."""

from pathlib import Path
from typing import Protocol

from inkbridge.core.models import InkDocument


class GoodnotesEncoder(Protocol):
    def encode(self, document: InkDocument, *, template: Path, output: Path) -> Path:
        """Write an importable archive containing native editable pen records."""
        ...
