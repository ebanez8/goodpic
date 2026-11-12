"""Six controlled archive experiments; diagnostic previews show inserted ink."""

import json
import struct
from pathlib import Path

from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint
from inkbridge.goodnotes.encoder import encode, encode_affine_clone
from inkbridge.goodnotes.geometry import place_document
from inkbridge.goodnotes.protobuf import fields, first
from inkbridge.goodnotes.reader import find_pen, inspect_pen
from inkbridge.rendering.reference import render, render_svg
from inkbridge.strokes.validation import load_json


def _document(paths: list[list[tuple[float, float]]], name: str) -> InkDocument:
    strokes = [Stroke(f"{name}-{i}", [StrokePoint(x, y, 1.6) for x, y in path],
                      (0, 0, 0, 1), "pen") for i, path in enumerate(paths)]
    return InkDocument(name, [Page(595.28, 841.89, "page_points_top_left", strokes)])


def _native_preview(points: list[tuple[float, float, float]], output: Path,
                    name: str, scale: float, color: tuple[float, float, float, float]):
    doc = InkDocument(name, [Page(595.28, 841.89, "page_points_top_left",
        [Stroke(name, [StrokePoint(x * scale, y * scale, w * 2 * scale)
                       for x, y, w in points], color, "pen")])])
    render(doc, page_index=0, output=output / "reference.png")
    render_svg(doc, page_index=0, output=output / "reference.svg")


def _write_report(directory: Path, report: dict[str, object]) -> None:
    (directory / "diagnostic.json").write_text(json.dumps(report, indent=2) + "\n")
    fields = report["modified_binary_fields"]
    assert isinstance(fields, list)
    source = report["source_pen"]
    assert isinstance(source, dict)
    (directory / "diagnostic.md").write_text(
        f"# {report['case']}\n\nNative archive: `result.goodnotes`. "
        "Reference: `reference.png` / `reference.svg`.\n\n"
        f"Source pen: `{source['source']}`.\n\n"
        "Modified fields in each inserted record:\n\n" +
        "".join(f"- {field}\n" for field in fields) +
        "\nZIP integrity and decoded geometry passed. Goodnotes rendering and "
        "partial erasing have not yet been checked.\n", encoding="utf-8")


def generate(*, template: Path, pen_source: Path, word_json: Path,
             output: Path, canvas_scale: float = 6 / 11) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    info = inspect_pen(pen_source, prefer_straight=True)
    pen = find_pen(pen_source, prefer_straight=True)
    sub = first(pen.content, 7)
    assert isinstance(sub, bytes)
    packed_color = first(sub, 4)
    assert isinstance(packed_color, bytes)
    rgba = [0.0, 0.0, 0.0, 1.0]
    for field in fields(packed_color):
        if 1 <= field.number <= 4 and isinstance(field.value, bytes):
            rgba[field.number - 1] = struct.unpack("<f", field.value)[0]
    files = []
    affine_cases = {
        "genuine_clone": (1, 0, 0, 1, 0, 0),
        "translated": (1, 0, 0, 1, 30, 20),
        "scaled": (1.25, 0, 0, 1.25, 0, 0),
    }
    for name, affine in affine_cases.items():
        directory = output / name
        directory.mkdir(exist_ok=True)
        result = encode_affine_clone(template=template, pen_source=pen_source,
                                     output=directory / "result.goodnotes", affine=affine)
        _native_preview(result.decoded_points[0], directory, name, canvas_scale,
                        (rgba[0], rgba[1], rgba[2], rgba[3]))
        report: dict[str, object] = {"case": name, "source_pen": info,
            "modified_binary_fields":
            ["shared metadata/pen field #1 UUID", "metadata field #8 destination document value",
             "metadata field #9 order", "linked metadata #2 and pen #15 tokens",
             "nested pen #7 token", "pen field #2 LZ4 geometry"] +
            ([] if name == "genuine_clone" else ["geometry anchor bytes",
                "sampled xy/radii bytes", "outline xy pair bytes",
                "control xy/radii/tangent bytes"]),
            "structural_validation": "decoded geometry and ZIP verified",
            "goodnotes_rendering": None}
        _write_report(directory, report)
        files.append(result.path)
    generated = {
        "straight": _document([[(80, 180), (250, 180)]], "straight"),
        "letter_a": _document([[(80, 160), (120, 80), (160, 160)],
                               [(96, 130), (144, 130)]], "letter-a"),
        "inksight_word": place_document(load_json(word_json)),
    }
    for name, doc in generated.items():
        directory = output / name
        directory.mkdir(exist_ok=True)
        result = encode(doc, template=template, pen_source=pen_source,
                        output=directory / "result.goodnotes", canvas_scale=canvas_scale)
        render(doc, page_index=0, output=directory / "reference.png")
        render_svg(doc, page_index=0, output=directory / "reference.svg")
        report = {"case": name, "source_pen": info,
            "stroke_count": len(doc.pages[0].strokes),
            "modified_binary_fields": ["shared metadata/pen field #1 UUID",
                "metadata field #8 destination document value and #9 order",
                "linked metadata #2 and pen #15 tokens, nested pen #7 token",
                "pen field #2 LZ4 geometry, #4 RGBA color",
                "geometry anchor bytes", "sampled xy/radii bytes", "outline xy pair bytes",
                "control xy/radii/tangent bytes"],
            "decoded_sampled_points": [len(points) for points in result.decoded_points],
            "structural_validation": "decoded geometry and ZIP verified",
            "goodnotes_rendering": None,
            "source_json": str(word_json) if name == "inksight_word" else None}
        _write_report(directory, report)
        files.append(result.path)
    return files
