"""Isolated InkSight worker. Run with the upstream environment's Python."""

import argparse
import importlib.util
import json
import os
import time
from pathlib import Path

from inkbridge.core.exceptions import InkBridgeError
from inkbridge.inksight.inkml_parser import parse_tokens
from inkbridge.preprocessing.image_loader import load_image, pad_for_inksight


class InkSightPredictor:
    """Hold one official SavedModel and use it for any number of images."""

    def __init__(self, model_path: Path):
        if not (model_path / "saved_model.pb").is_file():
            raise InkBridgeError(f"InkSight SavedModel missing at {model_path}")
        utility = Path(os.environ["INKSIGHT_UPSTREAM"]) / "utils" / "tensorflow.py"
        spec = importlib.util.spec_from_file_location("inksight_tensorflow", utility)
        if spec is None or spec.loader is None:
            raise InkBridgeError(f"Cannot load official TensorFlow configuration: {utility}")
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # official XLA configuration, without plotting imports
        except ImportError as exc:
            raise InkBridgeError(f"InkSight dependencies unavailable: {exc}") from exc
        tf = module.tf
        self.tf = tf
        self.model = tf.saved_model.load(str(model_path))
        self.serve = self.model.signatures["serving_default"]

    def predict(self, image: Path, *, prompt: str = "Recognize and derender.") -> dict:
        import numpy as np

        source = load_image(image)
        padded, transform = pad_for_inksight(source)
        encoded = self.tf.reshape(self.tf.io.encode_jpeg(np.asarray(padded)), (1, 1))
        started = time.perf_counter()
        text = self._run(encoded, prompt)
        try:
            traces = parse_tokens(text)
        except InkBridgeError:
            if prompt != "Recognize and derender.":
                raise
            traces = parse_tokens(self._run(encoded, "Derender the ink."))
        elapsed = time.perf_counter() - started
        strokes = []
        for trace in traces:
            strokes.append([list(transform.to_source(x, y)) for x, y in trace])
        return {"image_width": source.width, "image_height": source.height,
                "strokes": strokes, "inference_seconds": elapsed,
                "model": "Derendering/InkSight-Small-p",
                "model_revision": "8514f237f318b83fe3d27c49989daaa4de9dabb9"}

    def _run(self, encoded, prompt: str) -> str:
        result = self.serve(**{
            "input_text": self.tf.constant([prompt], dtype=self.tf.string),
            "image/encoded": encoded,
        })
        return result["output_0"].numpy()[0][0].decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    args = parser.parse_args()
    try:
        predictor = InkSightPredictor(args.model)
        result = predictor.predict(args.input)
        args.output.write_text(json.dumps(result), encoding="utf-8")
    except (InkBridgeError, KeyError, OSError, ValueError) as exc:
        parser.exit(1, f"InkSight inference failed: {exc}\n")


if __name__ == "__main__":
    main()
