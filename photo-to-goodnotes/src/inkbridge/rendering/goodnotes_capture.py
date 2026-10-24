"""Actual Goodnotes render ingress; initially supplied by a human."""

from pathlib import Path
from typing import Protocol


class GoodnotesRenderProvider(Protocol):
    def get_render(self, archive: Path, *, page_index: int) -> Path:
        """Return a screenshot or rasterized Goodnotes PDF page."""
        ...
