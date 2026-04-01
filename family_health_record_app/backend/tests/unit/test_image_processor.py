import io

from PIL import Image

from app.services.image_processor import desensitize_image


def _make_white_image(width: int = 100, height: int = 100) -> bytes:
    image = Image.new("RGB", (width, height), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_desensitize_image_masks_top_and_bottom():
    source = _make_white_image()
    output_bytes = desensitize_image(source, mask_top_percent=0.2, mask_bottom_percent=0.2)
    output_image = Image.open(io.BytesIO(output_bytes)).convert("RGB")

    top_pixel = output_image.getpixel((50, 5))
    middle_pixel = output_image.getpixel((50, 50))
    bottom_pixel = output_image.getpixel((50, 95))

    assert top_pixel == (0, 0, 0)
    assert middle_pixel != (0, 0, 0)
    assert bottom_pixel == (0, 0, 0)


def test_desensitize_image_returns_webp():
    source = _make_white_image()
    output_bytes = desensitize_image(source)
    output_image = Image.open(io.BytesIO(output_bytes))
    assert output_image.format == "WEBP"
