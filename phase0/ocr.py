"""On-screen text extraction — winocr primary (Windows.Media.Ocr), tesseract fallback.

winocr is ~12x faster than tesseract on this hardware (~330ms vs ~4s full-screen)
and far more accurate — it also fixes the garbled-text problem the VLM had. It's
built into Windows, CPU-only, no external binary. Runs off-thread in perception,
so its latency never blocks VISION.
"""
from __future__ import annotations
import io
import re
from PIL import Image
import config

# --- primary: winocr (Windows.Media.Ocr) --------------------------------------
try:
    import winocr
    _WINOCR = True
except Exception:
    _WINOCR = False

# --- fallback: tesseract ------------------------------------------------------
try:
    import pytesseract
    if config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    _TESS = True
except Exception:
    _TESS = False


def available() -> bool:
    return config.OCR_ENABLED and (_WINOCR or _TESS)


def _clean(raw: str) -> str:
    text = re.sub(r"[ \t]+", " ", raw)
    text = re.sub(r"\n\s*\n+", " / ", text).strip()
    text = text.replace("\n", " ")
    if len(text) > config.OCR_MAX_CHARS:
        text = text[: config.OCR_MAX_CHARS] + " ..."
    return text


def ocr_png(png_bytes: bytes) -> str:
    """Return cleaned, truncated OCR text for one frame (or '')."""
    if not available():
        return ""
    try:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception as e:
        return f"[ocr decode error: {e}]"
    if _WINOCR:
        try:
            return _clean(winocr.recognize_pil_sync(img)["text"])
        except Exception:
            pass  # fall through to tesseract
    if _TESS:
        try:
            return _clean(pytesseract.image_to_string(img))
        except Exception as e:
            return f"[ocr error: {e}]"
    return ""


if __name__ == "__main__":
    import sys
    print(f"winocr={_WINOCR} tesseract={_TESS}")
    print(ocr_png(open(sys.argv[1], "rb").read()))
