"""Image loading and the 224-square InkSight preprocessing transform."""

from dataclasses import dataclass
from pathlib import Path

from inkbridge.core.exceptions import InkBridgeError


@dataclass(frozen=True)
class ImageTransform:
    source_width: int
    source_height: int
    scale_x: float
    scale_y: float
    offset_x: int
    offset_y: int

    def to_source(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self.offset_x) / self.scale_x,
                (y - self.offset_y) / self.scale_y)


def load_image(path: Path):
    try:
        from PIL import Image, ImageOps

        with Image.open(path) as source:
            source.load()
            return ImageOps.exif_transpose(source).convert("RGB")
    except ImportError as exc:
        raise InkBridgeError("Pillow is required: pip install -e '.[image]'") from exc
    except (OSError, ValueError) as exc:
        raise InkBridgeError(f"Cannot load image {path}: {exc}") from exc


def pad_for_inksight(image):
    """Resize within 224x224 and center on white, as in the upstream notebook."""
    from PIL import Image

    width, height = image.size
    if width < 1 or height < 1:
        raise InkBridgeError("Image has no pixels")
    ratio = min(224 / width, 224 / height)
    scaled_width = max(1, int(width * ratio))
    scaled_height = max(1, int(height * ratio))
    resized = image.resize((scaled_width, scaled_height))
    left = (224 - scaled_width) // 2
    top = (224 - scaled_height) // 2
    canvas = Image.new("RGB", (224, 224), (255, 255, 255))
    canvas.paste(resized, (left, top))
    return canvas, ImageTransform(width, height, scaled_width / width,
                                  scaled_height / height, left, top)
