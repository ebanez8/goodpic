"""Download the pinned official Small-p SavedModel into the ignored model directory."""

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

REVISION = "8514f237f318b83fe3d27c49989daaa4de9dabb9"
DEFAULT_TARGET = Path(__file__).resolve().parents[1] / "models" / "pretrained" / "small-p"

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=DEFAULT_TARGET)
args = parser.parse_args()

snapshot_download("Derendering/InkSight-Small-p", revision=REVISION,
                  local_dir=args.output)
print(f"Model saved to {args.output} at revision {REVISION}")
