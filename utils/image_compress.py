"""Yuklangan rasmlarni siqish va o'lchamini kichiklashtirish."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_DIMENSION = 1600
JPEG_QUALITY = 85
WEBP_QUALITY = 85
PNG_COMPRESS_LEVEL = 6


def _resize_keep_aspect(image: Image.Image, max_dimension: int) -> Image.Image:
    width, height = image.size
    if width <= max_dimension and height <= max_dimension:
        return image
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return image


def _has_transparency(image: Image.Image) -> bool:
    if image.mode in ("RGBA", "LA"):
        return True
    if image.mode == "P" and "transparency" in image.info:
        return True
    return False


def _output_name(filename: str, fmt: str) -> str:
    stem = Path(filename or "image").stem or "image"
    ext = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
        "GIF": ".gif",
    }.get(fmt, ".jpg")
    return f"{stem}{ext}"


def compress_upload_file(file_obj, filename: str) -> tuple[BytesIO, str, int, int]:
    """Upload faylni siqib BytesIO qaytaradi: (buffer, filename, width, height)."""
    file_obj.seek(0)
    try:
        with Image.open(file_obj) as image:
            image = ImageOps.exif_transpose(image)
            image = _resize_keep_aspect(image, MAX_DIMENSION)

            if _has_transparency(image):
                fmt = "PNG"
                save_kwargs = {"optimize": True, "compress_level": PNG_COMPRESS_LEVEL}
            elif (filename or "").lower().endswith(".webp"):
                fmt = "WEBP"
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")
                save_kwargs = {"quality": WEBP_QUALITY, "method": 6}
            elif getattr(image, "is_animated", False):
                fmt = "GIF"
                save_kwargs = {"optimize": True}
            else:
                fmt = "JPEG"
                if image.mode != "RGB":
                    image = image.convert("RGB")
                save_kwargs = {"quality": JPEG_QUALITY, "optimize": True, "progressive": True}

            out = BytesIO()
            image.save(out, format=fmt, **save_kwargs)
            width, height = image.size
            out.seek(0)
            return out, _output_name(filename, fmt), width, height
    except UnidentifiedImageError:
        raise
    except OSError as exc:
        raise UnidentifiedImageError from exc
