"""InkBridge command-line entry point."""

# ruff: noqa: B008 -- Typer uses Option descriptors as parameter defaults.

import os
from pathlib import Path

import typer

from inkbridge.core.exceptions import InkBridgeError
from inkbridge.inksight.adapter import reconstruct
from inkbridge.rendering.reference import render, render_svg
from inkbridge.strokes.validation import load_json, save_json

app = typer.Typer(help="InkBridge handwriting reconstruction")


@app.command()
def status() -> None:
    """Show implemented pipeline stages."""
    typer.echo("Phase 1 InkSight and Phase 2 local Goodnotes tools available.")


@app.command("goodnotes")
def goodnotes_command(
    input: Path = typer.Option(..., "--input", exists=True, dir_okay=False),
    template: Path = typer.Option(..., "--template", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output"),
    pen_template: Path | None = typer.Option(None, "--pen-template", exists=True, dir_okay=False),
    canvas_scale: float = typer.Option(6 / 11, "--canvas-scale"),
    target_width: float = typer.Option(280, "--target-width", help="Word width on page in points"),
    placement: str = typer.Option("auto", "--placement", help="auto or preserve"),
    left: float = typer.Option(72, "--left", help="Placed word left edge in page points"),
    top: float = typer.Option(96, "--top", help="Placed word top edge in page points"),
    page_width: float = typer.Option(595.28, "--page-width"),
    page_height: float = typer.Option(841.89, "--page-height"),
) -> None:
    """Encode stroke JSON as native freehand pen records."""
    from inkbridge.goodnotes.encoder import encode
    from inkbridge.goodnotes.geometry import place_document

    try:
        document = load_json(input)
        if placement not in ("auto", "preserve"):
            raise ValueError("placement must be auto or preserve")
        if placement == "auto":
            document = place_document(document, target_width=target_width,
                                      left=left, top=top, page_width=page_width,
                                      page_height=page_height)
        result = encode(document, template=template, output=output,
                        pen_source=pen_template, canvas_scale=canvas_scale)
        render(document, page_index=0, output=output.with_name("reference.png"))
        render_svg(document, page_index=0, output=output.with_name("reference.svg"))
    except (InkBridgeError, OSError, ValueError, IndexError) as exc:
        typer.echo(f"Goodnotes encoding failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Wrote {result.path}; native pen records: {len(result.stroke_ids)}")
    typer.echo(f"Reference: {output.with_name('reference.png')}")


@app.command("compare")
def compare_command(
    reference: Path = typer.Option(..., "--reference", exists=True, dir_okay=False),
    actual: Path = typer.Option(..., "--actual", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output"),
    page: int = typer.Option(0, "--page"),
    crop: str | None = typer.Option(None, "--crop", help="x0,y0,x1,y1 screenshot pixels"),
    threshold: int = typer.Option(220, "--threshold"),
    align: bool = typer.Option(True, "--align/--no-align"),
) -> None:
    """Compare a reference with a real Goodnotes PDF export or screenshot."""
    from inkbridge.evaluation.comparison import compare

    try:
        rectangle = tuple(int(value) for value in crop.split(",")) if crop else None
        if rectangle is not None and len(rectangle) != 4:
            raise ValueError("crop requires four integers")
        report = compare(reference, actual, output, page_index=page,
                         crop=rectangle, threshold=threshold, align=align)
    except (OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"Comparison failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Raw IoU {report['raw']['iou']:.4f}; aligned IoU "
               f"{report['aligned']['iou']:.4f}; report: {output / 'report.md'}")


@app.command("geometry-experiments")
def geometry_experiments_command(
    template: Path = typer.Option(..., "--template", exists=True, dir_okay=False),
    pen_template: Path = typer.Option(..., "--pen-template", exists=True, dir_okay=False),
    word: Path = typer.Option(..., "--word", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output"),
    canvas_scale: float = typer.Option(6 / 11, "--canvas-scale"),
) -> None:
    """Generate clone, affine, straight, A, and InkSight word documents."""
    from inkbridge.goodnotes.experiments import generate

    try:
        files = generate(template=template, pen_source=pen_template, word_json=word,
                         output=output, canvas_scale=canvas_scale)
    except (OSError, ValueError, InkBridgeError) as exc:
        typer.echo(f"Geometry experiments failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo("\n".join(str(path) for path in files))


@app.command("candidate-grid")
def candidate_grid_command(
    input: Path = typer.Option(..., "--input", exists=True, dir_okay=False),
    template: Path = typer.Option(..., "--template", exists=True, dir_okay=False),
    pen_template: Path = typer.Option(..., "--pen-template", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output"),
) -> None:
    """Generate a small deterministic grid for later manual render scoring."""
    from inkbridge.goodnotes.geometry import place_document
    from inkbridge.optimization.experiments import generate_candidate
    from inkbridge.optimization.optimizer import default_candidates

    try:
        doc = place_document(load_json(input))
        for i, parameters in enumerate(default_candidates()):
            generate_candidate(doc, source_path=input, template=template,
                               pen_source=pen_template, output_dir=output,
                               candidate_id=f"candidate_{i:02d}", parameters=parameters)
    except (OSError, ValueError, InkBridgeError) as exc:
        typer.echo(f"Candidate generation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Generated 9 candidates under {output}")


@app.command("score-candidate")
def score_candidate_command(
    manifest: Path = typer.Option(..., "--manifest", exists=True, dir_okay=False),
    actual: Path = typer.Option(..., "--actual", exists=True, dir_okay=False),
    weights: Path | None = typer.Option(None, "--weights", exists=True, dir_okay=False,
                                        help="JSON metric-name to weight mapping"),
    page: int = typer.Option(0, "--page"),
    crop: str | None = typer.Option(None, "--crop"),
    threshold: int = typer.Option(220, "--threshold"),
    align: bool = typer.Option(True, "--align/--no-align"),
    goodnotes_version: str | None = typer.Option(None, "--goodnotes-version"),
) -> None:
    """Score a candidate using an actual supplied Goodnotes rendering."""
    import json

    from inkbridge.optimization.experiments import score_candidate

    try:
        metric_weights = json.loads(weights.read_text(encoding="utf-8")) if weights else None
        rectangle = tuple(int(value) for value in crop.split(",")) if crop else None
        if rectangle is not None and len(rectangle) != 4:
            raise ValueError("crop requires four integers")
        result = score_candidate(manifest, actual, metric_weights, page_index=page,
                                 crop=rectangle, threshold=threshold, align=align,
                                 goodnotes_version=goodnotes_version)
    except (OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"Candidate scoring failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Score {result['score']:.5f} (lower is better)")


@app.command("rank-candidates")
def rank_candidates_command(
    input: Path = typer.Option(..., "--input", exists=True, file_okay=False),
) -> None:
    """Rank candidates after real Goodnotes captures are supplied."""
    from inkbridge.optimization.experiments import rank_candidates

    for item in rank_candidates(input):
        typer.echo(f"{item['score']:.5f}  {item['candidate_id']}  {item['generated_file_path']}")


@app.command()
def inksight(
    input: Path = typer.Option(..., "--input", exists=True, dir_okay=False),
    output: Path = typer.Option(..., "--output"),
    dpi: float = typer.Option(..., "--dpi", help="Physical source-image DPI"),
    model: Path = typer.Option(Path("models/pretrained/small-p"), "--model"),
    upstream: Path = typer.Option(Path("external/inksight"), "--upstream"),
    python: Path = typer.Option(
        Path("external/inksight/.venv-wsl/bin/python" if os.name != "nt"
             else "external/inksight/.venv/Scripts/python.exe"), "--python"),
    pen_width: float = typer.Option(1.2, "--pen-width", help="Default diameter in page points"),
) -> None:
    """Reconstruct handwriting with Google's pretrained InkSight Small-p model."""
    try:
        document = reconstruct(input.resolve(), output_dir=output, python=python.absolute(),
                               model=model.resolve(), upstream=upstream.resolve(),
                               dpi=dpi, width_pt=pen_width)
        json_path = save_json(document, output / "strokes.json")
        png_path = render(document, page_index=0, output=output / "preview.png")
        svg_path = render_svg(document, page_index=0, output=output / "preview.svg")
    except (InkBridgeError, OSError, IndexError) as exc:
        typer.echo(f"InkSight failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    count = len(document.pages[0].strokes)
    points = sum(len(stroke.points) for stroke in document.pages[0].strokes)
    typer.echo(f"Strokes: {count}; points: {points}; inference: "
               f"{document.source_metadata['inference_seconds']:.2f}s")
    typer.echo(f"JSON: {json_path}\nPNG: {png_path}\nSVG: {svg_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
