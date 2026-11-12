"""Lossless ZIP-member cloning for Goodnotes documents."""

import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Archive:
    entries: list[tuple[zipfile.ZipInfo, bytes]]

    def names(self) -> list[str]:
        return [info.filename for info, _ in self.entries]

    def read(self, name: str) -> bytes:
        return next(data for info, data in self.entries if info.filename == name)

    def write(self, output: Path, replacements: dict[str, bytes]) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w") as archive:
            for info, data in self.entries:
                archive.writestr(info, replacements.get(info.filename, data))
        with zipfile.ZipFile(output) as check:
            if check.testzip() is not None:
                raise ValueError("written ZIP failed integrity check")
        return output


def open_archive(path: Path) -> Archive:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"corrupt Goodnotes ZIP: {path}")
        return Archive([(info, archive.read(info)) for info in archive.infolist()])
