"""Convert isolated InkSight pixel trajectories to the internal page contract."""

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

from inkbridge.core.exceptions import InkBridgeError
from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint
from inkbridge.preprocessing.image_loader import load_image


def normalize_prediction(raw: dict, image: Path, *, dpi: float,
                         width_pt: float = 1.2) -> InkDocument:
    if not math.isfinite(dpi) or dpi <= 0 or not math.isfinite(width_pt) or width_pt <= 0:
        raise InkBridgeError("DPI and pen width must be positive finite numbers")
    if not isinstance(raw, dict):
        raise InkBridgeError("Malformed InkSight prediction: expected an object")
    try:
        width = int(raw["image_width"])
        height = int(raw["image_height"])
        traces = raw["strokes"]
        if width <= 0 or height <= 0 or not isinstance(traces, list) or not traces:
            raise ValueError("missing image dimensions or strokes")
        factor = 72.0 / dpi
        strokes = []
        for index, trace in enumerate(traces):
            if not isinstance(trace, list) or not trace:
                raise ValueError(f"empty stroke {index}")
            points = []
            for pair in trace:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ValueError(f"invalid point in stroke {index}")
                x, y = float(pair[0]), float(pair[1])
                if not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError("non-finite point")
                points.append(StrokePoint(x * factor, y * factor, width_pt))
            strokes.append(Stroke(f"inksight-{index + 1}", points,
                                  (0.0, 0.0, 0.0, 1.0), "pen",
                                  {"width_source": "constant_default"}))
        page = Page(width * factor, height * factor, "page_points_top_left", strokes)
        elapsed = float(raw.get("inference_seconds", 0.0))
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("invalid inference duration")
        return InkDocument("inksight-reconstruction", [page], {
            "source": "Google InkSight Small-p", "image_path": str(image),
            "image_width_px": width, "image_height_px": height,
            "input_dpi": dpi, "dpi_source": "user_supplied",
            "model": str(raw.get("model", "Derendering/InkSight-Small-p")),
            "model_revision": str(raw.get("model_revision", "unknown")),
            "inference_seconds": elapsed,
            "pen_width_default_pt": width_pt,
        })
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise InkBridgeError(f"Malformed InkSight prediction: {exc}") from exc


def reconstruct(image: Path, *, output_dir: Path, python: Path, model: Path,
                upstream: Path, dpi: float, width_pt: float = 1.2) -> InkDocument:
    if not python.is_file():
        raise InkBridgeError(f"InkSight Python not found: {python}")
    if not (upstream / "utils" / "tensorflow.py").is_file():
        raise InkBridgeError(f"Official InkSight clone not found: {upstream}")
    if not (model / "saved_model.pb").is_file():
        raise InkBridgeError(f"InkSight weights not found: {model}")
    load_image(image)  # fail before launching the costly model
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="inksight-") as temp:
        response = Path(temp) / "prediction.json"
        env = os.environ.copy()
        source = Path(__file__).resolve().parents[2]
        env["PYTHONPATH"] = os.pathsep.join((str(source), str(upstream)))
        env["INKSIGHT_UPSTREAM"] = str(upstream)
        process = subprocess.run([
            str(python), "-m", "inkbridge.inksight.inference", "--input", str(image),
            "--output", str(response), "--model", str(model),
        ], capture_output=True, text=True, env=env, check=False)
        if process.returncode:
            raise InkBridgeError(f"InkSight worker failed ({process.returncode}): "
                                 f"{process.stderr.strip() or process.stdout.strip()}")
        try:
            raw = json.loads(response.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise InkBridgeError(f"InkSight worker gave no valid JSON: {exc}") from exc
    return normalize_prediction(raw, image, dpi=dpi, width_pt=width_pt)
