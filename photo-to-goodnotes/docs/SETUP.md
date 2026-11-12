# Setup

Use Python 3.11 for the core project. On Windows run `./scripts/bootstrap.ps1`; on Linux, macOS, or WSL run `bash scripts/bootstrap.sh`. The scripts create `.venv` if absent and install `.[dev]`; they do not copy or overwrite `.env`. Activate the environment and run `python scripts/check_environment.py`. Optional groups: `pip install -e ".[image,optimization]"` and, only for training work, `pip install -e ".[training]"`.

Dependency ranges in `pyproject.toml` are provisional compatibility bounds, not a resolved lock. `uv` is not installed in the inspected workspace, so no lock was generated or validated here. For a reproducible project environment, run `uv lock` on Python 3.11 and commit the resulting `uv.lock` after resolution; InkSight has its own upstream `uv.lock`. Do not use the parent repository's packaging environment.

For the implemented Phase 1 inference, follow [InkSight setup](INKSIGHT.md). It pins the official source and checkpoint, describes a minimal isolated TensorFlow environment, and gives the tested WSL command. `scripts/setup_inksight.ps1` or `.sh` remain available for the full upstream `uv sync --locked` environment. Bootstrap does not download weights.
