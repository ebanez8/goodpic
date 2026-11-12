"""Antialias-tolerant visual metrics for real supplied app captures."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import distance_transform_edt  # type: ignore[import-untyped]
from skimage.metrics import structural_similarity

from inkbridge.rendering.alignment import bounds, ink_mask

MetricName = Literal["chamfer", "iou", "pixel_difference", "ssim", "stroke_bbox"]


@dataclass(frozen=True, slots=True)
class MetricResult:
    name: MetricName
    value: float
    lower_is_better: bool


def calculate(reference: Image.Image, actual: Image.Image,
              *, threshold: int = 220) -> list[MetricResult]:
    if reference.size != actual.size:
        actual = actual.resize(reference.size, Image.Resampling.LANCZOS)
    a = ink_mask(reference, threshold)
    b = ink_mask(actual, threshold)
    union = np.count_nonzero(a | b)
    iou = float(np.count_nonzero(a & b) / union) if union else 1.0
    diagonal = float(np.hypot(*reference.size)) or 1.0
    if not a.any() and not b.any():
        chamfer = 0.0
    elif not a.any() or not b.any():
        chamfer = 1.0
    else:
        chamfer = float((distance_transform_edt(~b)[a].mean() +
                         distance_transform_edt(~a)[b].mean()) / (2 * diagonal))
    left = np.asarray(reference.convert("L").filter(ImageFilter.GaussianBlur(0.75)), dtype=float)
    right = np.asarray(actual.convert("L").filter(ImageFilter.GaussianBlur(0.75)), dtype=float)
    pixel = float(np.abs(left - right).mean() / 255)
    ssim = (float(structural_similarity(left, right, data_range=255))
            if min(left.shape) >= 7 else 1 - pixel)
    box_a, box_b = bounds(a), bounds(b)
    if box_a is None and box_b is None:
        bbox = 0.0
    elif box_a is None or box_b is None:
        bbox = 1.0
    else:
        bbox = float(np.mean(np.abs(np.asarray(box_a) - np.asarray(box_b))) / diagonal)
    return [MetricResult("iou", iou, False), MetricResult("chamfer", chamfer, True),
            MetricResult("pixel_difference", pixel, True), MetricResult("ssim", ssim, False),
            MetricResult("stroke_bbox", bbox, True)]
