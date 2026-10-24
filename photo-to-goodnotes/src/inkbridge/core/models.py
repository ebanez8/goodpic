"""Stable internal handwriting data contracts (schema version 1)."""

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

Metadata: TypeAlias = dict[str, str | int | float | bool | None]
ColorRGBA: TypeAlias = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class StrokePoint:
    x: float
    y: float
    width: float
    pressure: float | None = None
    timestamp: float | None = None


@dataclass(slots=True)
class Stroke:
    id: str
    points: list[StrokePoint]
    color: ColorRGBA
    tool: str
    metadata: Metadata = field(default_factory=dict)


@dataclass(slots=True)
class Page:
    width: float
    height: float
    coordinate_system: Literal["page_points_top_left"]
    strokes: list[Stroke]
    background_reference: str | None = None


@dataclass(slots=True)
class InkDocument:
    id: str
    pages: list[Page]
    source_metadata: Metadata = field(default_factory=dict)
    schema_version: str = "1.0"
