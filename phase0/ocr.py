"""Phase 1 OCR — exact on-screen text via tesseract (local, deterministic).

Complements the VLM narration: moondream paraphrases the scene, OCR nails the
literal strings (stack traces, paths, commands, values). Runs on the laptop.
"""
from __future__ import annotations
import io
import re
from PIL import Image
import config

try:
    import pytesseract
    if config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    _OK = True
except Exception:  # pytesseract or binary missing
    _OK = False


def available() -> bool:
    return _OK and config.OCR_ENABLED


def ocr_png(png_bytes: bytes) -> str:
    """Return cleaned, truncated OCR text for one keyframe (or '')."""
    if not available():
        return ""
    try:
        img = Image.open(io.BytesIO(png_bytes))
        raw = pytesseract.image_to_string(img)
    except Exception as e:
        return f"[ocr error: {e}]"
    # collapse whitespace/blank lines into a compact single-line-ish blob
    text = re.sub(r"[ \t]+", " ", raw)
    text = re.sub(r"\n\s*\n+", " ‹› ", text).strip()  # blank lines -> ‹›
    text = text.replace("\n", " ")
    if len(text) > config.OCR_MAX_CHARS:
        text = text[: config.OCR_MAX_CHARS] + " …"
    return text


if __name__ == "__main__":
    import sys
    print(ocr_png(open(sys.argv[1], "rb").read()))
