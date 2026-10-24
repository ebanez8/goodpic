"""Candidate encoder controls; units follow the internal page-point convention."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EncoderParameters:
    scale_x: float = 1.0
    scale_y: float = 1.0
    translate_x: float = 0.0
    translate_y: float = 0.0
    width_scale: float = 1.0
    curve_tension: float | None = None
    control_point_scale: float | None = None
    geometry_encoding_variant: str | None = None
