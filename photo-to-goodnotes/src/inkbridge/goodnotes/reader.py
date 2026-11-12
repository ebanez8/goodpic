"""Read native page records without discarding unknown fields."""

import math
from dataclasses import dataclass
from pathlib import Path

from inkbridge.goodnotes.archive import Archive, open_archive
from inkbridge.goodnotes.compression import decompress
from inkbridge.goodnotes.geometry import layout, sampled_points
from inkbridge.goodnotes.protobuf import first, records


@dataclass(frozen=True)
class PenTemplate:
    metadata: bytes
    content: bytes
    geometry: bytes
    source: Path
    page_member: str
    record_index: int


def page_members(archive: Archive) -> list[str]:
    return [name for name in archive.names() if name.startswith("notes/")
            and not name.endswith("/")]


def choose_page(archive: Archive) -> str:
    for name in page_members(archive):
        if records(archive.read(name)):
            return name
    raise ValueError("document has no populated notes page")


def find_pen(path: Path, *, prefer_straight: bool = False) -> PenTemplate:
    archive = open_archive(path)
    for name in page_members(archive):
        recs = records(archive.read(name))
        candidates: list[tuple[float, PenTemplate]] = []
        for index, rec in enumerate(recs):
            sub = first(rec, 7)
            if not isinstance(sub, bytes) or first(sub, 21) != 24:
                continue
            blob = first(sub, 2)
            if not isinstance(blob, bytes):
                continue
            try:
                raw = decompress(blob)
                info = layout(raw)
            except (ValueError, IndexError):
                continue
            if info.count < 8:
                continue
            if index == 0 or first(recs[index - 1], 1) is None:
                continue
            pen = PenTemplate(recs[index - 1], rec, raw, path, name, index)
            if not prefer_straight:
                return pen
            points = sampled_points(raw)
            length = sum(math.dist(a[:2], b[:2]) for a, b in zip(
                points, points[1:], strict=False))
            straightness = math.dist(points[0][:2], points[-1][:2]) / length if length else 0
            if len(points) >= 24 and straightness >= 0.98:
                candidates.append((straightness, pen))
        if candidates:
            return max(candidates, key=lambda item: item[0])[1]
    qualifier = "near-straight " if prefer_straight else ""
    raise ValueError(f"no supported {qualifier}genuine freehand pen record in {path}")


def inspect_pen(path: Path, *, prefer_straight: bool = False) -> dict:
    pen = find_pen(path, prefer_straight=prefer_straight)
    points = sampled_points(pen.geometry)
    info = layout(pen.geometry)
    return {"source": str(path), "page_member": pen.page_member,
            "record_index": pen.record_index, "point_count": info.count,
            "outline_pair_count": (info.outline_end - info.outline) // 8,
            "control_record_count": info.count,
            "geometry_byte_ranges": {"anchor": [info.anchor, info.anchor + 12],
                "sampled_path": [info.points, info.points + 12 * info.count],
                "outline_pairs": [info.outline, info.outline_end],
                "control_records": [info.controls, info.controls + 20 * info.count]},
            "bounds": [min(p[0] for p in points), min(p[1] for p in points),
                       max(p[0] for p in points), max(p[1] for p in points)]}
