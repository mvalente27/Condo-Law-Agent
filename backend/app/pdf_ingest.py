"""PDF ingestion: extract text, OCR fallback for scanned legacy deeds."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import fitz  # PyMuPDF

from .config import get_settings


@dataclass
class PageText:
    page: int
    text: str
    ocr_used: bool


def _ocr_page(page: "fitz.Page", dpi: int, lang: str) -> str:
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return ""
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    try:
        return pytesseract.image_to_string(img, lang=lang)
    except Exception:
        return ""


def extract_pdf(data: bytes) -> list[PageText]:
    settings = get_settings()
    out: list[PageText] = []
    with fitz.open(stream=BytesIO(data).read(), filetype="pdf") as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            ocr_used = False
            if len(text.strip()) < 40 and settings.ocr_enabled:
                ocr_text = _ocr_page(page, settings.ocr_dpi, settings.ocr_lang)
                if ocr_text.strip():
                    text = ocr_text
                    ocr_used = True
            out.append(PageText(page=i, text=text, ocr_used=ocr_used))
    return out
