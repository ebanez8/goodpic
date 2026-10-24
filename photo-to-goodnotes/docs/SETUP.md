# Setup

Use Python 3.11 for the core project. On Windows run `./scripts/bootstrap.ps1`; on Linux, macOS, or WSL run `bash scripts/bootstrap.sh`. The scripts create `.venv` if absent and install `.[dev]`; they do not copy or overwrite `.env`. Activate the environment and run `python scripts/check_environment.py`. Optional groups: `pip install -e ".[image,optimization]"` and, only for training work, `pip install -e ".[training]"`.

Dependency ranges in `pyproject.toml` are provisional compatibility bounds, not a resolved lock. `uv` is not installed in the inspected workspace, so no lock was generated or validated here. For a reproducible project environment, run `uv lock` on Python 3.11 and commit the resulting `uv.lock` after resolution; InkSight has its own upstream `uv.lock`. Do not use the parent repository's packaging environment.

For InkSight, see `scripts/setup_inksight.ps1` or `.sh` and [ML pipeline](ML_PIPELINE.md). Current upstream specifies Python `>=3.11,<3.14`, TensorFlow 2.20.0, TensorFlow Text 2.20.1, and `python-doctr[tf,viz]==0.10.0`; use its own `uv sync`. Its package declares `tensorflow[and-cuda]`, which targets Linux CUDA. Native Windows GPU support is not established by those instructions; WSL2/Linux is the practical GPU path. CPU inference should be validated separately when implemented. No weights are downloaded by bootstrap.
