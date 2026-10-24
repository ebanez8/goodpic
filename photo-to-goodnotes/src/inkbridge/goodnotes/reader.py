"""Future archive reader preserving unknown records and metadata."""

from pathlib import Path
from typing import Protocol


class GoodnotesReader(Protocol):
    def read(self, archive_path: Path) -> bytes:
        """Return an opaque, losslessly preservable archive representation."""
        ...
