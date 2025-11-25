import io
import tempfile
from pathlib import Path
from typing import Literal

from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import asyncio


FileType = Literal["pdf", "image"]


async def ocr_file(file_bytes: bytes, file_type: FileType) -> str:
    """
    Run OCR on an uploaded file (PDF or image) and return extracted text.
    Uses asyncio.to_thread to keep FastAPI endpoints async-friendly.
    """
    if file_type == "image":
        return await asyncio.to_thread(_ocr_image_bytes, file_bytes)
    elif file_type == "pdf":
        return await asyncio.to_thread(_ocr_pdf_bytes, file_bytes)
    else:
        raise ValueError(f"Unsupported file_type: {file_type}")


def _ocr_image_bytes(file_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image, lang="eng")
    return text


def _ocr_pdf_bytes(file_bytes: bytes) -> str:
    # Write PDF to a temp file for pdf2image
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "input.pdf"
        pdf_path.write_bytes(file_bytes)

        images = convert_from_path(str(pdf_path))
        texts: list[str] = []
        for img in images:
            page_text = pytesseract.image_to_string(img, lang="eng")
            texts.append(page_text)

    return "\n\n".join(texts)
