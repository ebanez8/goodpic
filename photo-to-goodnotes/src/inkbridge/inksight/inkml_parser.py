"""Future parser for InkML, if confirmed as an inference output format."""

from pathlib import Path
from typing import Protocol

from inkbridge.core.models import InkDocument


class InkMLParser(Protocol):
    def parse(self, path: Path) -> InkDocument: ...
