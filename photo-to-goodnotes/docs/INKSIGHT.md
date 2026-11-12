# Phase 1: InkSight reconstruction

This stage runs Google's pretrained **InkSight Small-p** SavedModel. The official
inference repository is pinned here to commit
`486d4772e2fdd187f0c3416a41479b1ffc080c66`; the Hugging Face checkpoint
`Derendering/InkSight-Small-p` is pinned to revision
`8514f237f318b83fe3d27c49989daaa4de9dabb9`. The worker uses the official
`serving_default` signature and prompts, and the notebook's 224-grid token
decoder. Live inference emits `<ink_token_N>` text; InkML is a format of the
published example outputs, not the live SavedModel response.

## Setup

Use Python 3.11 or 3.12 for both environments. Keep the core CLI and TensorFlow
in separate virtual environments. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
first. In WSL2/Ubuntu or Linux:

```bash
git clone https://github.com/google-research/inksight.git external/inksight
cd external/inksight
git checkout 486d4772e2fdd187f0c3416a41479b1ffc080c66
uv venv --python 3.12 ~/inksight-venv
uv pip install --python ~/inksight-venv/bin/python tensorflow==2.20.0 tensorflow-text==2.20.1 tf-keras==2.20.1 huggingface_hub==0.36.0 pillow numpy
cd ../..
~/inksight-venv/bin/python scripts/download_inksight_model.py --output ~/inksight-model
uv venv --python 3.12 ~/inkbridge-venv
uv pip install --python ~/inkbridge-venv/bin/python -e '.[image,dev]'
```

The model download is about 692 MB. `scripts/setup_inksight.sh` offers the
upstream full `uv sync --locked` environment as an alternative. It includes
OCR and notebook dependencies. On native Windows, run the core CLI with a
Windows core environment and an InkSight worker environment if TensorFlow Text
can be installed there; WSL2/Linux is the recommended and tested path. On WSL,
create virtual environments in the Linux filesystem; `/mnt/c` can reject package
metadata writes.
TensorFlow automatically uses a compatible GPU if its CUDA runtime is present;
otherwise it runs on CPU. The minimal dependency command above does not install
CUDA libraries. For GPU, install them in the worker environment with
`uv pip install --python ~/inksight-venv/bin/python 'tensorflow[and-cuda]==2.20.0'`
in WSL2/Linux, then verify GPU visibility with `nvidia-smi` and
`tf.config.list_physical_devices('GPU')`.

## Run

From this project directory in WSL2/Linux:

```bash
~/inkbridge-venv/bin/inkbridge inksight --input external/inksight/test_inputs/word.jpg --output generated/inksight_test --dpi 300 --python ~/inksight-venv/bin/python --model ~/inksight-model
```

The official sample has no calibrated physical page scale for this project;
`300` in this example is a user-selected output scale, not a measured photo DPI.

Use a clear, upright crop of one handwritten word or short line. InkSight's
word-level path fits the image into a 224 × 224 square with white padding, so
full-page photographs become too small for reliable reconstruction. The source
image is not copied into the preview. Supported image formats are those Pillow
can read, including PNG and JPEG; EXIF rotation is applied. Supply the actual
source-image DPI via `--dpi`. If a camera photo has no calibrated DPI, choose a
target scale explicitly and treat the page size as approximate. No pixel-to-point
conversion is assumed. `--pen-width` sets the constant output diameter in page
points (default 1.2 pt).

Outputs in the chosen directory are `strokes.json`, `preview.png`, and
`preview.svg`. The JSON follows [schema v1](DATA_FORMATS.md). It records source
image dimensions, DPI, model name, and inference seconds. Points are ordered
within each individual stroke. InkSight does not predict pressure, timestamps,
width, or color in this checkpoint; pressure and timestamp are `null`, and the
width and black color are explicit defaults. The preview is drawn on a white
canvas from the JSON stroke geometry. No smoothing or resampling is applied.

The worker loads the checkpoint once per process. `InkSightPredictor` may be
reused for multiple images in one worker process; each CLI invocation starts a
fresh process. Failures loading the checkpoint, missing TensorFlow operators,
bad images, and empty token output are reported as errors rather than producing
an empty document. Extremely large photos still reduce to the model's 224-grid,
so fine detail can be lost.

## Verification on 2026-10-23

The official `test_inputs/word.jpg` sample was run with the pinned checkpoint
on WSL2 CPU at a user-selected 300 DPI output scale. It produced 8 strokes and
504 ordered points, plus JSON, PNG, and SVG previews; model inference took
701.72 seconds. The PNG visibly reads "Neat:". These results use the upstream
sample image, not the user's notes. The fixture-based unit suite passed 7 tests.
TensorFlow detected an NVIDIA GeForce RTX 3050 Ti Laptop GPU after installing
the `tensorflow[and-cuda]==2.20.0` extra in the isolated worker environment.
The GPU run on the same sample produced 7 strokes and 505 points in 71.59
seconds; `nvidia-smi` showed 97% GPU utilization during inference. Its preview
also reads "Neat:". CPU and GPU traces differed slightly in stroke boundaries
and point count, so outputs should not be assumed bit-for-bit identical across
hardware.
