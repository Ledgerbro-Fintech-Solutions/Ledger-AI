import io
import base64
from typing import List
from PIL import Image
import fitz  # PyMuPDF

from backend.app.core.config import settings
from backend.app.core.logging import logger


def encode_image_pil(image: Image.Image) -> str:
    """Encode PIL image to base64 JPEG string."""
    buffered = io.BytesIO()
    # Convert RGBA / P mode images to RGB before saving as JPEG
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format=settings.image_format, quality=settings.image_quality)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def bytes_to_image(image_bytes: bytes) -> Image.Image:
    """Load PIL Image from raw bytes."""
    try:
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.error(f"Error opening image from bytes: {e}")
        raise ValueError(f"Invalid image format: {e}")


def pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert multi-page PDF bytes to a list of PIL Images."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        matrix = fitz.Matrix(settings.pdf_zoom_factor, settings.pdf_zoom_factor)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        doc.close()
        logger.info(f"Rendered {len(images)} page(s) from PDF.")
        return images
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise ValueError(f"Unable to parse PDF document: {e}")


def is_pdf_file(content_type: str, filename: str = "") -> bool:
    """Check if content type or file extension signifies a PDF."""
    if content_type and "pdf" in content_type.lower():
        return True
    if filename and filename.lower().endswith(".pdf"):
        return True
    return False
