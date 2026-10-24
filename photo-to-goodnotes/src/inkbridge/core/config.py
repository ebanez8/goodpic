"""Configuration file shape; loading and precedence are not implemented."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    data_dir: Path
    generated_dir: Path
    experiments_dir: Path
