"""Candidate archives and manifests, with manual actual-render feedback."""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint
from inkbridge.evaluation.comparison import compare
from inkbridge.goodnotes.encoder import encode
from inkbridge.optimization.objective import score
from inkbridge.optimization.parameters import EncoderParameters
from inkbridge.rendering.reference import render, render_svg
from inkbridge.strokes.validation import save_json


def parameterized(document: InkDocument, parameters: EncoderParameters) -> InkDocument:
    if min(parameters.scale_x, parameters.scale_y, parameters.width_scale) <= 0:
        raise ValueError("scales and width_scale must be positive")
    pages = []
    for page in document.pages:
        strokes = [Stroke(id=s.id, color=s.color, tool=s.tool, metadata=s.metadata.copy(),
                          points=[StrokePoint(p.x * parameters.scale_x + parameters.translate_x,
                                              p.y * parameters.scale_y + parameters.translate_y,
                                              p.width * parameters.width_scale,
                                              p.pressure, p.timestamp) for p in s.points])
                   for s in page.strokes]
        pages.append(Page(page.width, page.height, page.coordinate_system, strokes,
                          page.background_reference))
    return InkDocument(document.id, pages, document.source_metadata.copy(), document.schema_version)


def generate_candidate(document: InkDocument, *, source_path: Path, template: Path,
                       pen_source: Path, output_dir: Path, candidate_id: str,
                       parameters: EncoderParameters, canvas_scale: float = 6 / 11,
                       goodnotes_version: str | None = None) -> Path:
    directory = output_dir / candidate_id
    directory.mkdir(parents=True, exist_ok=True)
    transformed = parameterized(document, parameters)
    save_json(transformed, directory / "strokes.json")
    result = encode(transformed, template=template, pen_source=pen_source,
                    output=directory / "result.goodnotes", canvas_scale=canvas_scale)
    render(transformed, page_index=0, output=directory / "reference.png")
    render_svg(transformed, page_index=0, output=directory / "reference.svg")
    manifest = {"candidate_id": candidate_id, "source_stroke_data": str(source_path.resolve()),
                "input_stroke_data": str((directory / "strokes.json").resolve()),
                "encoder_parameters": asdict(parameters),
                "generated_file_path": str(result.path.resolve()),
                "reference_rendering": str((directory / "reference.png").resolve()),
                "actual_rendering": None, "visual_metrics": None, "score": None,
                "goodnotes_version": goodnotes_version,
                "created_utc": datetime.now(UTC).isoformat(),
                "geometry_layout": "vA_52_sample_warp", "canvas_scale": canvas_scale}
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def score_candidate(manifest_path: Path, actual: Path,
                    weights: dict[str, float] | None = None, *, page_index: int = 0,
                    crop: tuple[int, int, int, int] | None = None,
                    threshold: int = 220, align: bool = True,
                    goodnotes_version: str | None = None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = compare(Path(manifest["reference_rendering"]), actual,
                      manifest_path.parent / "comparison", page_index=page_index,
                      crop=crop, threshold=threshold, align=align)
    manifest["actual_rendering"] = str(actual.resolve())
    if goodnotes_version is not None:
        manifest["goodnotes_version"] = goodnotes_version
    manifest["visual_metrics"] = metrics
    manifest["comparison_settings"] = {"page_index": page_index,
                                       "crop": crop, "threshold": threshold,
                                       "align": align, "weights": weights}
    objective_metrics = dict(metrics["aligned"])
    objective_metrics["stroke_bbox"] = metrics["raw"]["stroke_bbox"]
    manifest["score"] = score(objective_metrics, weights)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def rank_candidates(directory: Path) -> list[dict]:
    records = [json.loads(path.read_text(encoding="utf-8"))
               for path in directory.glob("*/manifest.json")]
    return sorted((item for item in records if item.get("score") is not None),
                  key=lambda item: item["score"])
