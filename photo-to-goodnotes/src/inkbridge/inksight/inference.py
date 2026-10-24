"""Future isolated worker: model acquisition/loading and image inference."""

from pathlib import Path
from typing import Protocol


class TrajectoryPredictor(Protocol):
    def predict(self, image: Path, *, output: Path) -> Path:
        """Write native InkSight output and return its location."""
        ...
