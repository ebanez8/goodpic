from PIL import Image, ImageDraw

from inkbridge.evaluation.comparison import compare
from inkbridge.evaluation.metrics import calculate
from inkbridge.rendering.alignment import align_translation
from inkbridge.rendering.goodnotes_capture import load_capture
from inkbridge.rendering.reference import render
from inkbridge.strokes.validation import load_json


def shape(offset=(0, 0), scale=1.0, distorted=False):
    im = Image.new("RGB", (128, 128), "white")
    draw = ImageDraw.Draw(im)
    x, y = offset
    draw.line([(int(x + 20 * scale), int(y + 20 * scale)),
               (int(x + 100 * scale), int(y + (80 if distorted else 100) * scale))],
              fill="black", width=5)
    return im


def metric_map(a, b):
    return {metric.name: metric.value for metric in calculate(a, b)}


def test_identical_translated_scaled_distorted_and_empty():
    reference = shape()
    assert metric_map(reference, reference)["iou"] == 1
    translated = shape(offset=(6, 4))
    raw = metric_map(reference, translated)
    aligned, shift = align_translation(reference, translated)
    assert shift == (-6, -4)
    assert metric_map(reference, aligned)["iou"] > raw["iou"]
    assert metric_map(reference, shape(scale=0.8))["iou"] < 1
    assert metric_map(reference, shape(distorted=True))["chamfer"] > 0
    blank = Image.new("RGB", (128, 128), "white")
    assert metric_map(blank, blank)["iou"] == 1
    assert metric_map(blank, reference)["chamfer"] == 1
    assert metric_map(reference, reference.resize((64, 64)))["iou"] < 1


def test_comparison_artifacts_and_reference_render(tmp_path):
    reference = tmp_path / "ref.png"
    actual = tmp_path / "actual.png"
    shape().save(reference)
    shape(offset=(5, 3)).save(actual)
    report = compare(reference, actual, tmp_path / "comparison")
    assert report["raw"]["iou"] < report["aligned"]["iou"]
    assert all((tmp_path / "comparison" / name).exists() for name in
               ("reference.png", "actual.png", "aligned.png", "overlay.png",
                "difference.png", "metrics.json", "report.md"))


def test_reference_width_color_and_size(tmp_path):
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    document = load_json(root / "tests" / "fixtures" / "ink_document.json")
    out = render(document, page_index=0, output=tmp_path / "reference.png",
                 pixels_per_point=1)
    image = Image.open(out)
    assert image.size == (596, 842)
    assert image.getpixel((72, 72)) != (255, 255, 255)
    alpha = Image.open(render(document, page_index=0, output=tmp_path / "transparent.png",
                              pixels_per_point=1, transparent=True))
    assert alpha.getpixel((0, 0))[3] == 0


def test_pdf_capture_page_and_crop(tmp_path):
    path = tmp_path / "capture.pdf"
    shape().save(path, "PDF")
    captured = load_capture(path, page_index=0, target_size=(128, 128))
    assert captured.size == (128, 128)
    assert metric_map(shape(), captured)["iou"] > 0.5
    cropped = load_capture(path, page_index=0, crop=(10, 10, 110, 110))
    assert cropped.size == (100, 100)


def test_reference_stroke_order_and_rgba(tmp_path):
    from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint

    first = Stroke("red", [StrokePoint(10, 10, 8)], (1, 0, 0, 1), "pen")
    second = Stroke("blue", [StrokePoint(10, 10, 4)], (0, 0, 1, 1), "pen")
    doc = InkDocument("colors", [Page(20, 20, "page_points_top_left", [first, second])])
    image = Image.open(render(doc, page_index=0, output=tmp_path / "colors.png",
                              pixels_per_point=4))
    assert image.getpixel((40, 40)) == (0, 0, 255)
    assert image.getpixel((54, 40)) == (255, 0, 0)
