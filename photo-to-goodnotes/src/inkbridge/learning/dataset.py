"""Future paired target/actual render training samples."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TrainingSample:
    target_strokes: Path
    actual_render: Path
    encoder_configuration: Path


class SampleLoader(Protocol):
    def load(self, manifest: Path) -> list[TrainingSample]: ...
