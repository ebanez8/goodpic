"""Future pipeline composition; manual render handoff is an explicit boundary."""

from pathlib import Path
from typing import Protocol


class ConversionPipeline(Protocol):
    def generate_candidate(self, image: Path, *, template: Path, output: Path) -> Path: ...
