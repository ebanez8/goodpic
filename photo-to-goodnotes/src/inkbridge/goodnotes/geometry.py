"""Measured vA freehand geometry; unsupported layouts fail closed."""

import math
import struct
from dataclasses import dataclass

from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint


@dataclass(frozen=True)
class PenLayout:
    anchor: int
    points: int
    outline: int
    outline_end: int
    controls: int
    count: int


def layout(raw: bytes) -> PenLayout:
    if len(raw) < 100 or raw[:4] != b"tpl\0" or raw[8:12] != b"vA(v":
        raise ValueError("unsupported Goodnotes pen geometry layout")
    if struct.unpack_from("<I", raw, 4)[0] != len(raw):
        raise ValueError("pen geometry length mismatch")
    flags = struct.unpack_from("<I", raw, 52)[0]
    anchor = 60 + 2 * flags
    if anchor + 16 >= len(raw) or struct.unpack_from("<H", raw, anchor - 4)[0] != 3:
        raise ValueError("unexpected pen anchor header")
    float_count = struct.unpack_from("<I", raw, anchor + 12)[0]
    if float_count < 6 or float_count % 3:
        raise ValueError("invalid pen point count")
    count = float_count // 3
    points = anchor + 16
    offset = points + 12 * count
    for _ in range(2):
        if offset + 4 > len(raw):
            raise ValueError("truncated pen flags")
        offset += 4 + 2 * struct.unpack_from("<I", raw, offset)[0]
    if offset + 4 > len(raw) or struct.unpack_from("<I", raw, offset)[0] != count:
        raise ValueError("pen companion count differs from sampled path")
    outline = offset + 4
    controls = -1
    marker = struct.pack("<I", 5 * count)
    for candidate in range(outline, len(raw) - 4, 8):
        if raw[candidate:candidate + 4] != marker:
            continue
        tail = candidate + 4 + 20 * count
        if tail + 4 + 2 * count == len(raw) and struct.unpack_from("<I", raw, tail)[0] == count:
            controls = candidate + 4
            break
    if controls < 0:
        raise ValueError("unsupported pen outline/control layout")
    return PenLayout(anchor, points, outline, controls - 4, controls, count)


def sampled_points(raw: bytes) -> list[tuple[float, float, float]]:
    info = layout(raw)
    return [struct.unpack_from("<fff", raw, info.points + i * 12)
            for i in range(info.count)]


def resample(points: list[StrokePoint], count: int) -> list[StrokePoint]:
    if not points:
        raise ValueError("empty stroke")
    if len(points) == 1:
        center = points[0]
        radius = center.width * 0.02
        return [StrokePoint(center.x + radius * (2 * i / (count - 1) - 1),
                            center.y, center.width) for i in range(count)]
    lengths = [0.0]
    for a, b in zip(points, points[1:], strict=False):
        lengths.append(lengths[-1] + math.hypot(b.x - a.x, b.y - a.y))
    if lengths[-1] == 0:
        return resample(points[:1], count)
    result = []
    segment = 0
    for i in range(count):
        distance = lengths[-1] * i / (count - 1)
        while segment < len(points) - 2 and lengths[segment + 1] < distance:
            segment += 1
        a, b = points[segment:segment + 2]
        fraction = (distance - lengths[segment]) / max(
            1e-12, lengths[segment + 1] - lengths[segment])
        result.append(StrokePoint(a.x + fraction * (b.x - a.x),
                                  a.y + fraction * (b.y - a.y),
                                  a.width + fraction * (b.width - a.width)))
    return result


def place_document(document: InkDocument, *, target_width: float = 280,
                   left: float = 72, top: float = 96,
                   page_width: float = 595.28, page_height: float = 841.89,
                   auto: bool = True) -> InkDocument:
    """Fit a small photo-derived word onto an A4 page; retain pen diameters."""
    if not math.isfinite(target_width) or target_width <= 0:
        raise ValueError("target_width must be positive")
    page = document.pages[0]
    if auto and page.width >= 200 and page.height >= 200:
        return document
    xs = [point.x for stroke in page.strokes for point in stroke.points]
    ys = [point.y for stroke in page.strokes for point in stroke.points]
    if not xs:
        raise ValueError("cannot place an empty page")
    scale = target_width / max(max(xs) - min(xs), 1e-6)
    scale = min(scale, (page_height - top - 72) / max(max(ys) - min(ys), 1e-6))
    strokes = [Stroke(s.id, [StrokePoint(left + (p.x - min(xs)) * scale,
                                       top + (p.y - min(ys)) * scale,
                                       p.width, p.pressure, p.timestamp)
                             for p in s.points], s.color, s.tool, s.metadata.copy())
               for s in page.strokes]
    new_page = Page(page_width, page_height, "page_points_top_left", strokes,
                    page.background_reference)
    return InkDocument(document.id, [new_page], document.source_metadata.copy(),
                       document.schema_version)


def _frame(path: list[tuple[float, float, float]], x: float, y: float):
    best = None
    for i, (a, b) in enumerate(zip(path, path[1:], strict=False)):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / length2)) if length2 else 0.0
        px, py = a[0] + t * dx, a[1] + t * dy
        distance2 = (x - px) ** 2 + (y - py) ** 2
        if best is None or distance2 < best[0]:
            length = math.sqrt(length2) or 1.0
            nx, ny = -dy / length, dx / length
            best = (distance2, i, t, nx, ny, (x - px) * nx + (y - py) * ny)
    assert best is not None
    return best


def transform(raw: bytes, target: list[StrokePoint], *, canvas_scale: float,
              affine: tuple[float, float, float, float, float, float] | None = None) -> bytes:
    """Transform sampled path, outline pairs, and five-float control records."""
    info = layout(raw)
    source = sampled_points(raw)
    result = bytearray(raw)
    if affine is None:
        mapped = resample(target, info.count)
        dest = [(p.x / canvas_scale, p.y / canvas_scale,
                 p.width / (2 * canvas_scale)) for p in mapped]

        def map_point(x: float, y: float) -> tuple[float, float]:
            _, i, t, nx, ny, offset = _frame(source, x, y)
            a, b = dest[i:i + 2]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy) or 1.0
            tx, ty = -dy / length, dx / length
            width_ratio = (a[2] + t * (b[2] - a[2])) / max(
                0.05, source[i][2] + t * (source[i + 1][2] - source[i][2]))
            return (a[0] + t * dx + tx * offset * width_ratio,
                    a[1] + t * dy + ty * offset * width_ratio)
    else:
        a, b, c, d, e, f = affine
        width_factor = math.sqrt(abs(a * d - b * c))
        dest = [(a * x + b * y + e, c * x + d * y + f, w * width_factor)
                for x, y, w in source]

        def map_point(x: float, y: float) -> tuple[float, float]:
            return a * x + b * y + e, c * x + d * y + f

    x, y, w = struct.unpack_from("<fff", raw, info.anchor)
    mx, my = map_point(x, y)
    struct.pack_into("<fff", result, info.anchor, mx, my,
                     dest[0][2] if affine is None else w * width_factor)
    for i, point in enumerate(dest):
        struct.pack_into("<fff", result, info.points + 12 * i, *point)
    for offset in range(info.outline, info.outline_end, 8):
        first_word, second_word = struct.unpack_from("<II", raw, offset)
        if first_word == 0 and 0 < second_word < 1_000_000:
            continue  # Outline ring marker stored as integers, not coordinates.
        x, y = struct.unpack_from("<ff", raw, offset)
        struct.pack_into("<ff", result, offset, *map_point(x, y))
    for i in range(info.count):
        offset = info.controls + 20 * i
        x, y, w, tx, ty = struct.unpack_from("<fffff", raw, offset)
        mx, my = map_point(x, y)
        if affine is not None:
            ntx, nty, nw = a * tx + b * ty, c * tx + d * ty, w * width_factor
        else:
            _, j, t, _, _, _ = _frame(source, x, y)
            sx, sy = source[j + 1][0] - source[j][0], source[j + 1][1] - source[j][1]
            dx, dy = dest[j + 1][0] - dest[j][0], dest[j + 1][1] - dest[j][1]
            angle = math.atan2(dy, dx) - math.atan2(sy, sx)
            nw = dest[j][2] + t * (dest[j + 1][2] - dest[j][2])
            factor = nw / max(w, 0.05)
            ntx = factor * (math.cos(angle) * tx - math.sin(angle) * ty)
            nty = factor * (math.sin(angle) * tx + math.cos(angle) * ty)
        struct.pack_into("<fffff", result, offset, mx, my, nw, ntx, nty)
    return bytes(result)
