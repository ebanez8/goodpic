"""Future renderer for normalized target strokes."""

from pathlib import Path
from typing import Protocol

from inkbridge.core.models import InkDocument


class ReferenceRenderer(Protocol):
    def render(self, document: InkDocument, *, page_index: int, output: Path) -> Path: ...
