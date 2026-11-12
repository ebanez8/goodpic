"""Actual-versus-reference comparison and reproducible image artifacts."""

import json
from pathlib import Path

import numpy as np
from PIL import Image

from inkbridge.evaluation.metrics import calculate
from inkbridge.rendering.alignment import align_translation, ink_mask
from inkbridge.rendering.goodnotes_capture import load_capture


def compare(reference: Path, actual: Path, output: Path, *, page_index: int = 0,
            crop: tuple[int, int, int, int] | None = None,
            threshold: int = 220, align: bool = True) -> dict:
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be 0..255")
    target = load_capture(reference)
    observed = load_capture(actual, page_index=page_index, crop=crop,
                            target_size=target.size)
    aligned, shift = align_translation(target, observed, threshold) if align else (observed, (0, 0))
    raw_metrics = calculate(target, observed, threshold=threshold)
    aligned_metrics = calculate(target, aligned, threshold=threshold)
    output.mkdir(parents=True, exist_ok=True)
    target.save(output / "reference.png")
    observed.save(output / "actual.png")
    aligned.save(output / "aligned.png")
    a, b = ink_mask(target, threshold), ink_mask(aligned, threshold)
    overlay = np.full((*a.shape, 3), 255, dtype=np.uint8)
    overlay[a & ~b] = (220, 30, 30)
    overlay[b & ~a] = (30, 80, 220)
    overlay[a & b] = (20, 20, 20)
    Image.fromarray(overlay).save(output / "overlay.png")
    difference = np.abs(np.asarray(target.convert("L"), dtype=np.int16) -
                        np.asarray(aligned.convert("L"), dtype=np.int16)).astype(np.uint8)
    Image.fromarray(difference).save(output / "difference.png")
    raw_values = {m.name: m.value for m in raw_metrics}
    aligned_values = {m.name: m.value for m in aligned_metrics}
    report = {"reference": str(reference), "actual": str(actual),
              "actual_source": "user_supplied_goodnotes_export_or_screenshot",
              "alignment_shift_pixels": list(shift), "threshold": threshold,
              "raw": raw_values, "aligned": aligned_values}
    (output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "report.md").write_text(
        f"# Visual comparison\n\nActual source: {actual}\n\n"
        f"Alignment shift: {shift[0]}, {shift[1]} pixels.\n\n"
        f"Raw IoU: {raw_values['iou']:.4f}; aligned IoU: {aligned_values['iou']:.4f}.\n\n"
        "Raw scores expose placement differences; aligned scores emphasize shape. "
        "Red in overlay is missing actual ink, blue is extra actual ink.\n",
        encoding="utf-8")
    return report
