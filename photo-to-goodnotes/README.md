# InkBridge

Foundation for converting handwriting photographs into native editable Goodnotes ink. This directory is a separate Python project because the workspace root already contains the unrelated `goodparse` application. No pipeline stage or Goodnotes writer is implemented yet.

## Quick start

Windows: `./scripts/bootstrap.ps1` from this directory. Linux/macOS/WSL: `bash scripts/bootstrap.sh`. Both create `.venv` and install the local package with development tools. Then run `python scripts/check_environment.py` using the virtual environment's Python. See [setup](docs/SETUP.md).

The future flow is image -> isolated InkSight process -> internal `InkDocument` -> Goodnotes encoder -> manual Goodnotes render -> evaluation -> optimization. The only executable interface today is `inkbridge --help`; commands do not convert files.

The historical `t/` experiment described by the project brief was not present in this checkout on 2026-10-21. The repository root contains `samples/` and `src/goodparse/`; they were not moved or changed. See [experiment history](docs/EXPERIMENT_HISTORY.md).
