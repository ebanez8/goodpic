"""Boundary between the core process and an isolated InkSight worker."""

from pathlib import Path
from typing import Protocol

from inkbridge.core.models import InkDocument


class InkSightAdapter(Protocol):
    def reconstruct(self, image: Path, *, output_dir: Path) -> InkDocument:
        """Request trajectories for an image and normalize them to schema v1."""
        ...
