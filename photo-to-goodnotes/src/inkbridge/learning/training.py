"""Future trainer and checkpoint lifecycle."""

from pathlib import Path
from typing import Protocol


class Trainer(Protocol):
    def train(self, manifest: Path, *, checkpoint_dir: Path) -> Path: ...
