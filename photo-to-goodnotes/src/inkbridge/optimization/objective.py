"""Future objective composition for measured visual metrics."""

from typing import Protocol

from inkbridge.evaluation.metrics import MetricResult


class Objective(Protocol):
    def score(self, metrics: list[MetricResult]) -> float: ...
