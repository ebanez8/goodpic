# Testing strategy

Run the local suite from this directory with `.venv/Scripts/python.exe -m pytest -q --basetemp generated/phase2_pytest_tmp -p no:cacheprovider` on Windows, or `pytest -q` where the system temp directory is writable. The suite checks protobuf unknown-field preservation, Apple LZ4, genuine pen geometry, affine companion transforms, ZIP member preservation, inserted record counts and UUIDs, decoded coordinates and widths, reference rendering, comparison metrics, and the Phase 1 adapter. It does not import anything into Goodnotes. The current Windows system temp and `.pytest_cache` directories are permission blocked, so the workspace-local temp flag is necessary here.

`tests/fixtures/inksight_word.json` is a saved seven-stroke output from Google's official `word.jpg`, generated with the pretrained Small-p model. Its absolute input path was replaced with a relative path. Integration tests do not rerun inference. Recreate the six revised diagnostic archives in `generated/phase2_experiments_v2/` with the README command. Each folder contains `result.goodnotes`, `reference.png`, `reference.svg`, `diagnostic.json`, and `diagnostic.md`. The reference shows only newly inserted ink. Follow [manual Goodnotes testing](MANUAL_GOODNOTES_CHECKLIST.md) and save actual app exports separately.

Phase 1 unit tests are in `tests/unit/test_inksight_phase1.py`. They use small
synthetic token, InkML, image, and prediction fixtures; they do not run the
checkpoint. Run `pytest tests/unit/test_inksight_phase1.py`. For a real model
check, use the official `external/inksight/test_inputs/word.jpg` as shown in
[InkSight setup](INKSIGHT.md), then inspect `strokes.json` and `preview.png`.
