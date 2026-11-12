"""Blank-canvas reference previews drawn solely from vector strokes."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

from inkbridge.core.exceptions import InkBridgeError
from inkbridge.core.models import InkDocument


def render(document: InkDocument, *, page_index: int, output: Path,
           pixels_per_point: float = 2.0, transparent: bool = False) -> Path:
    from PIL import Image, ImageDraw

    if not math.isfinite(pixels_per_point) or pixels_per_point <= 0:
        raise InkBridgeError("pixels_per_point must be positive")
    page = document.pages[page_index]
    image = Image.new("RGBA", (max(1, math.ceil(page.width * pixels_per_point)),
                               max(1, math.ceil(page.height * pixels_per_point))),
                      (255, 255, 255, 0) if transparent else "white")
    draw = ImageDraw.Draw(image)
    for stroke in page.strokes:
        rgba = tuple(round(channel * 255) for channel in stroke.color)
        color = rgba if transparent else tuple(round(rgba[i] * rgba[3] / 255 +
            255 * (1 - rgba[3] / 255)) for i in range(3)) + (255,)
        points = stroke.points
        for first, second in zip(points, points[1:], strict=False):
            distance = math.hypot(second.x - first.x, second.y - first.y)
            steps = max(1, math.ceil(distance * pixels_per_point / 2))
            for i in range(steps + 1):
                t = i / steps
                x = (first.x + t * (second.x - first.x)) * pixels_per_point
                y = (first.y + t * (second.y - first.y)) * pixels_per_point
                radius = (first.width + t * (second.width - first.width)) * pixels_per_point / 2
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        for point in (points if len(points) == 1 else (points[0], points[-1])):
            radius = point.width * pixels_per_point / 2
            x, y = point.x * pixels_per_point, point.y * pixels_per_point
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not transparent:
        image = image.convert("RGB")
    image.save(output)
    return output


def render_svg(document: InkDocument, *, page_index: int, output: Path,
               transparent: bool = False) -> Path:
    page = document.pages[page_index]
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}svg", {"viewBox": f"0 0 {page.width} {page.height}",
                                         "width": str(page.width), "height": str(page.height)})
    if not transparent:
        ET.SubElement(root, f"{{{ns}}}rect", {"width": "100%", "height": "100%", "fill": "white"})
    for stroke in page.strokes:
        color = "#{:02x}{:02x}{:02x}".format(*(round(c * 255) for c in stroke.color[:3]))
        coords = " ".join(f"{point.x},{point.y}" for point in stroke.points)
        if len(stroke.points) == 1:
            point = stroke.points[0]
            ET.SubElement(root, f"{{{ns}}}circle", {"cx": str(point.x), "cy": str(point.y),
                "r": str(point.width / 2), "fill": color,
                "fill-opacity": str(stroke.color[3])})
        elif all(abs(point.width - stroke.points[0].width) < 1e-6 for point in stroke.points):
            ET.SubElement(root, f"{{{ns}}}polyline", {"points": coords, "fill": "none",
                "stroke": color, "stroke-opacity": str(stroke.color[3]),
                "stroke-width": str(stroke.points[0].width),
                "stroke-linecap": "round", "stroke-linejoin": "round"})
        else:
            group = ET.SubElement(root, f"{{{ns}}}g", {"fill": color,
                "fill-opacity": str(stroke.color[3])})
            for a, b in zip(stroke.points, stroke.points[1:], strict=False):
                distance = math.hypot(b.x - a.x, b.y - a.y)
                steps = max(1, math.ceil(distance))
                for i in range(steps + 1):
                    t = i / steps
                    ET.SubElement(group, f"{{{ns}}}circle", {
                        "cx": str(a.x + t * (b.x - a.x)),
                        "cy": str(a.y + t * (b.y - a.y)),
                        "r": str((a.width + t * (b.width - a.width)) / 2)})
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    return output
