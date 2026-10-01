"""Small Pillow helpers used by the seed/import commands."""
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageOps


def optimized_jpeg(path, max_size=1600, quality=82):
    """Open a trusted local image, fix phone-camera rotation, shrink it and return a ContentFile (JPEG)."""
    Image.MAX_IMAGE_PIXELS = 250_000_000  # local camera photos can be very large
    with Image.open(path) as img:
        img.draft("RGB", (max_size * 2, max_size * 2))  # fast JPEG down-scaled decode
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
    return ContentFile(buffer.getvalue())


def placeholder_jpeg(text, size=(1600, 800)):
    """A simple sky-blue → black gradient image, used when no photo is available."""
    width, height = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    top, bottom = (3, 105, 161), (10, 10, 10)
    for y in range(height):
        t = y / height
        draw.line([(0, y), (width, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    draw.text((60, height - 120), text, fill=(224, 242, 254))
    buffer = BytesIO()
    img.save(buffer, "JPEG", quality=85)
    return ContentFile(buffer.getvalue())
