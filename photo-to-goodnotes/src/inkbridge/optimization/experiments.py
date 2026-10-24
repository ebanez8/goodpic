"""Tracking schema for Goodnotes render experiments."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from inkbridge.evaluation.metrics import MetricResult
from inkbridge.optimization.parameters import EncoderParameters


@dataclass(slots=True)
class ExperimentRecord:
    experiment_id: str
    input_stroke_data: Path
    encoder_configuration: EncoderParameters
    generated_file_path: Path
    actual_rendered_image_path: Path | None
    calculated_metrics: list[MetricResult] = field(default_factory=list)
    timestamp: datetime | None = None
    notes: str = ""
    goodnotes_version: str | None = None
