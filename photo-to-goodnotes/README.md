# InkBridge

InkBridge converts InkSight stroke JSON into native Goodnotes pen records and provides local rendering and visual comparison tools. This directory is a separate Python project from the workspace root `goodparse` application.

## Quick start

Windows: `./scripts/bootstrap.ps1` from this directory. Linux/macOS/WSL: `bash scripts/bootstrap.sh`. Both create `.venv` and install the local package with development tools. Then run `python scripts/check_environment.py` using the virtual environment's Python. See [setup](docs/SETUP.md).

Phase 1 is implemented: image -> isolated InkSight process -> internal `InkDocument` -> JSON and vector preview. See [InkSight setup and inference](docs/INKSIGHT.md).

Phase 2 writes native pen records from `InkDocument` strokes. Generated paths use a near-straight genuine freehand record from `samples/Test5.goodnotes`; the document template can be a separate archive. The output page is cleared before new pen records are inserted. The local tests establish archive structure and decoded geometry. The first app import showed that loop-based path warping did not render, so visual compatibility of the revised files and partial erasing remain unverified. See [format notes](docs/GOODNOTES_FORMAT.md) and [manual checklist](docs/MANUAL_GOODNOTES_CHECKLIST.md).

```bash
inkbridge goodnotes --input generated/inksight_word/strokes.json \
  --template ../samples/test.goodnotes --pen-template ../samples/Test5.goodnotes \
  --output generated/goodnotes/word.goodnotes

inkbridge geometry-experiments --template ../samples/test.goodnotes \
  --pen-template ../samples/Test5.goodnotes --word tests/fixtures/inksight_word.json \
  --output generated/phase2_experiments_v2

inkbridge compare --reference generated/phase2_experiments_v2/letter_a/reference.png \
  --actual path/to/goodnotes-export.pdf --page 0 \
  --output generated/reports/letter_a
```

`goodnotes` auto-fits small photo-derived pages to a 280 pt wide word at page position (72, 96), preserving pen diameter. Use `--placement preserve` to retain internal page coordinates, or `--target-width`, `--left`, `--top`, `--page-width`, and `--page-height` to choose placement. The default canvas/page scale is `6/11`, measured on the supplied sample archives; override it with `--canvas-scale` for other templates. The reference preview contains exactly the new ink; existing template page marks are omitted from the generated document.

For candidate studies, run `inkbridge candidate-grid`, then `inkbridge score-candidate --manifest ... --actual ...` for each real app export and `inkbridge rank-candidates --input ...`. No optimizer is launched without real render feedback.

The historical `t/` experiment described by the project brief was not present in this checkout on 2026-10-30. The repository root contains `samples/` and `src/goodparse/`; they were not moved or changed. See [experiment history](docs/EXPERIMENT_HISTORY.md).
