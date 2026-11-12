"""Weighted score, lower is better, only for real supplied renderings."""

DEFAULT_WEIGHTS = {"iou": 0.35, "chamfer": 0.25, "pixel_difference": 0.15,
                   "ssim": 0.15, "stroke_bbox": 0.10}


def score(metrics: dict[str, float], weights: dict[str, float] | None = None) -> float:
    weights = weights or DEFAULT_WEIGHTS
    if not isinstance(weights, dict) or any(
            not isinstance(value, (int, float)) for value in weights.values()):
        raise ValueError("weights must map metric names to numbers")
    if not weights or sum(weights.values()) <= 0 or any(value < 0 for value in weights.values()):
        raise ValueError("metric weights must be nonnegative and nonempty")
    missing = set(weights) - set(metrics)
    if missing:
        raise ValueError(f"missing metrics: {sorted(missing)}")
    return sum(weight * (1 - metrics[name] if name in ("iou", "ssim") else metrics[name])
               for name, weight in weights.items()) / sum(weights.values())
