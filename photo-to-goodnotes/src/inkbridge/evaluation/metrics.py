"""Metric names and result contract; calculations are not implemented."""

from dataclasses import dataclass
from typing import Literal, Protocol

MetricName = Literal["chamfer", "iou", "pixel_difference", "ssim", "stroke_bbox"]


@dataclass(frozen=True, slots=True)
class MetricResult:
    name: MetricName
    value: float
    lower_is_better: bool


class VisualMetric(Protocol):
    def calculate(self, target: bytes, actual: bytes) -> MetricResult: ...
