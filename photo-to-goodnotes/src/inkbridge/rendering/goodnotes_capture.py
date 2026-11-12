"""Manual Goodnotes PDF/screenshot intake; no simulated app rendering."""

from pathlib import Path

from PIL import Image


def load_capture(path: Path, *, page_index: int = 0,
                 crop: tuple[int, int, int, int] | None = None,
                 target_size: tuple[int, int] | None = None) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".pdf":
        try:
            import pypdfium2 as pdfium  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError("PDF capture requires pypdfium2 (install inkbridge[image])") from exc
        pdf = pdfium.PdfDocument(str(path))
        if not 0 <= page_index < len(pdf):
            raise ValueError(f"PDF page {page_index} is out of range")
        page = pdf[page_index]
        scale = target_size[0] / page.get_width() if target_size else 2.0
        image = page.render(scale=scale).to_pil().convert("RGBA")
        pdf.close()
    else:
        image = Image.open(path).convert("RGBA")
    if crop is not None:
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
            raise ValueError("capture crop lies outside the image")
        image = image.crop(crop)
    if target_size and image.size != target_size:
        image = image.resize(target_size, Image.Resampling.LANCZOS)
    background = Image.new("RGBA", image.size, "white")
    return Image.alpha_composite(background, image).convert("RGB")
