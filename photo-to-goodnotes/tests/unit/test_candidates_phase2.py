import json
from pathlib import Path

import pytest

from inkbridge.optimization.experiments import generate_candidate, rank_candidates
from inkbridge.optimization.objective import score
from inkbridge.optimization.parameters import EncoderParameters
from inkbridge.strokes.validation import load_json

ROOT = Path(__file__).resolve().parents[2]


def test_candidate_manifest_without_app_feedback(tmp_path):
    source = ROOT / "tests" / "fixtures" / "ink_document.json"
    document = load_json(source)
    manifest = generate_candidate(document, source_path=source,
        template=ROOT.parent / "samples" / "test.goodnotes",
        pen_source=ROOT.parent / "samples" / "Test5.goodnotes",
        output_dir=tmp_path, candidate_id="base", parameters=EncoderParameters())
    data = json.loads(manifest.read_text())
    assert Path(data["generated_file_path"]).exists()
    assert Path(data["reference_rendering"]).exists()
    assert data["score"] is None
    assert rank_candidates(tmp_path) == []
    data["score"] = 0.2
    manifest.write_text(json.dumps(data))
    assert rank_candidates(tmp_path)[0]["candidate_id"] == "base"


def test_objective_weights():
    metrics = {"iou": 1.0, "chamfer": 0.0, "pixel_difference": 0.0,
               "ssim": 1.0, "stroke_bbox": 0.0}
    assert score(metrics) == 0
    metrics["iou"] = 0.5
    assert score(metrics) > 0
    with pytest.raises(ValueError):
        score(metrics, {"iou": 0})
