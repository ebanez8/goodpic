"""Explicit template selection; a vector line is never accepted as a pen."""

from pathlib import Path

from inkbridge.goodnotes.reader import PenTemplate, find_pen


def pen_template(document_template: Path, pen_source: Path | None = None) -> PenTemplate:
    return find_pen(pen_source or document_template)
