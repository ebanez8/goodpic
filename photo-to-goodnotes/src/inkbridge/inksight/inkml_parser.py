"""Parse InkSight's live token output and saved InkML traces."""

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from inkbridge.core.exceptions import InkBridgeError

_TOKEN = re.compile(r"<ink_token_(\d+)>")
_INKML = "{http://www.w3.org/2003/InkML}"


def parse_tokens(output: str) -> list[list[tuple[float, float]]]:
    """Decode the official Small-p 224-grid stream, preserving pen-up markers."""
    tokens = [int(value) for value in _TOKEN.findall(output)]
    if not tokens:
        raise InkBridgeError("InkSight returned no ink tokens")
    if any(value > 450 for value in tokens):
        raise InkBridgeError("InkSight returned an out-of-range ink token")
    strokes: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    index = 0
    while index < len(tokens):
        if tokens[index] == 450:
            if current:
                strokes.append(current)
            current = []
            index += 1
        elif index + 1 < len(tokens) and tokens[index + 1] != 450:
            x, y = tokens[index], tokens[index + 1] - 225
            if 0 <= x <= 224 and 0 <= y <= 224:
                current.append((float(x), float(y)))
            index += 2
        else:
            index += 1
    if current:
        strokes.append(current)
    if not strokes:
        raise InkBridgeError("InkSight returned no usable strokes")
    return strokes


def parse_inkml(path: Path) -> list[list[tuple[float, float]]]:
    """Read official sample InkML while retaining trace and point order."""
    try:
        root = ET.parse(path).getroot()
        traces = root.findall(f"{_INKML}trace")
        if not traces:
            raise ValueError("no InkML traces")
        strokes = []
        for trace in traces:
            if not trace.text or not trace.text.strip():
                raise ValueError("empty InkML trace")
            points = []
            for item in trace.text.strip().split():
                parts = item.split(",")
                if len(parts) != 2:
                    raise ValueError(f"invalid InkML point: {item}")
                x, y = map(float, parts)
                if not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError("non-finite InkML coordinate")
                points.append((x, y))
            strokes.append(points)
        return strokes
    except (ET.ParseError, ValueError) as exc:
        raise InkBridgeError(f"Malformed InkML in {path}: {exc}") from exc
