"""Simple ink bounding-box alignment with a preserved raw comparison."""

import numpy as np
from PIL import Image


def ink_mask(image: Image.Image, threshold: int = 220) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    return np.min(rgb, axis=2) < threshold


def bounds(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def align_translation(reference: Image.Image, actual: Image.Image,
                      threshold: int = 220) -> tuple[Image.Image, tuple[int, int]]:
    target_box = bounds(ink_mask(reference, threshold))
    actual_box = bounds(ink_mask(actual, threshold))
    if target_box is None or actual_box is None:
        return actual.copy(), (0, 0)
    dx = round((target_box[0] + target_box[2] - actual_box[0] - actual_box[2]) / 2)
    dy = round((target_box[1] + target_box[3] - actual_box[1] - actual_box[3]) / 2)
    result = Image.new("RGB", reference.size, "white")
    result.paste(actual, (dx, dy))
    return result, (dx, dy)
