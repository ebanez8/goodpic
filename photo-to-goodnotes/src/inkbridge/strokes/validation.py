"""Validate and serialize the v1 InkDocument contract."""

import json
import math
from dataclasses import asdict
from pathlib import Path

from inkbridge.core.exceptions import InkBridgeError
from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint


def validate(document: InkDocument) -> None:
    if document.schema_version != "1.0" or not document.pages:
        raise InkBridgeError("Expected a schema v1 document with at least one page")
    ids = set()
    for page in document.pages:
        if page.coordinate_system != "page_points_top_left":
            raise InkBridgeError("Unsupported coordinate system")
        if not all(math.isfinite(v) and v > 0 for v in (page.width, page.height)):
            raise InkBridgeError("Invalid page size")
        for stroke in page.strokes:
            if not stroke.id or stroke.id in ids or not stroke.points:
                raise InkBridgeError("Duplicate stroke ID or empty stroke")
            ids.add(stroke.id)
            if len(stroke.color) != 4 or any(not math.isfinite(v) or v < 0 or v > 1
                                              for v in stroke.color):
                raise InkBridgeError("Invalid stroke color")
            for point in stroke.points:
                if not all(math.isfinite(v) for v in (point.x, point.y, point.width)):
                    raise InkBridgeError("Non-finite stroke point")
                if point.width <= 0:
                    raise InkBridgeError("Invalid stroke width")
                if point.pressure is not None and not 0 <= point.pressure <= 1:
                    raise InkBridgeError("Invalid pressure")


def save_json(document: InkDocument, output: Path) -> Path:
    validate(document)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(document), indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    return output


def load_json(path: Path) -> InkDocument:
    """Load a saved v1 document without coupling the encoder to InkSight."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        pages = [Page(width=p["width"], height=p["height"],
                      coordinate_system=p["coordinate_system"],
                      background_reference=p.get("background_reference"),
                      strokes=[Stroke(id=s["id"], tool=s["tool"], color=tuple(s["color"]),
                                      metadata=s.get("metadata", {}),
                                      points=[StrokePoint(**point) for point in s["points"]])
                               for s in p["strokes"]]) for p in raw["pages"]]
        document = InkDocument(id=raw["id"], pages=pages,
                               source_metadata=raw.get("source_metadata", {}),
                               schema_version=raw.get("schema_version", "1.0"))
        validate(document)
        return document
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise InkBridgeError(f"invalid stroke JSON {path}: {exc}") from exc
