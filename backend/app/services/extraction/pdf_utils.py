import base64
import io
from typing import Optional
from PIL import Image
import pypdfium2 as pdfium


def convert_pdf_to_images(
    pdf_bytes: bytes,
    max_pages: int = 5,
    target_dpi: int = 150,
) -> list[Image.Image]:
    """Rasterize PDF pages to PIL Images."""
    pdf = pdfium.PdfDocument(pdf_bytes)
    total_pages = min(len(pdf), max_pages)
    images: list[Image.Image] = []

    # 72 dpi is standard points scale in PDF; target_dpi / 72 gives scale factor
    scale = target_dpi / 72.0

    for i in range(total_pages):
        page = pdf[i]
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        images.append(pil_image)

    return images


def image_to_base64(image: Image.Image, format: str = "JPEG", quality: int = 85) -> str:
    """Convert PIL Image to base64 data string."""
    buffered = io.BytesIO()
    # Convert RGBA to RGB for JPEG compatibility
    if format.upper() == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format=format, quality=quality)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def pdf_to_base64_images(pdf_bytes: bytes, max_pages: int = 3) -> list[str]:
    """Convert first N pages of PDF to base64 JPEG strings."""
    images = convert_pdf_to_images(pdf_bytes, max_pages=max_pages)
    return [image_to_base64(img) for img in images]
