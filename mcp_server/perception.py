"""Shared Tier-1 perception core: continuous local screen translation.

Runs a background thread that samples the full screen, keeps changed frames
(pHash), narrates each on rick's local VLM, and stores lines in a rolling
buffer + timeline.log. Both the standalone Phase-0 loop and the MCP server use
this. No hosted calls; nothing leaves the LAN.
"""
from __future__ import annotations
import io
import sys
import time
import threading
from pathlib import Path
from collections import deque
from datetime import datetime, timezone

import mss
import imagehash
from PIL import Image

# allow importing phase0's config + narrator without duplicating them
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "phase0"))
import config              # noqa: E402
from narrator import narrate  # noqa: E402

TIMELINE = Path(__file__).resolve().parent.parent / "phase0" / "timeline.log"

_stream: deque[str] = deque(maxlen=500)
_lock = threading.Lock()
_started = False


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _png(img: Image.Image, w: int) -> bytes:
    if img.width > w:
        img = img.resize((w, int(img.height * w / img.width)))
    b = io.BytesIO()
    img.save(b, format="PNG")
    return b.getvalue()


def _emit(source: str, text: str) -> str:
    line = f"[{_ts()}] {source:<6} {text}"
    with _lock:
        _stream.append(line)
    try:
        with TIMELINE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    return line


def _grab_png():  # -> (png_bytes, phash)
    with mss.mss() as sct:
        mon = sct.monitors[config.MONITOR_INDEX]
        shot = sct.grab(mon)
        img = Image.frombytes("RGB", shot.size, shot.rgb)
        return _png(img, config.DOWNSCALE_WIDTH), imagehash.phash(img)


def snapshot_now() -> str:
    """Capture + narrate the current frame immediately; return the narration."""
    png, _ = _grab_png()
    text = narrate(png).replace("\n", " | ")
    _emit("VISION", text + "  (on-demand)")
    return text


def recent(lines: int = 12) -> str:
    """Return the last `lines` of the rolling translated stream as text."""
    with _lock:
        window = list(_stream)[-lines:]
    return "\n".join(window) if window else "(stream empty — perception just started)"


def _loop() -> None:
    last_hash = None
    while True:
        try:
            png, h = _grab_png()
            if last_hash is None or (h - last_hash) >= config.HASH_DIFF_THRESHOLD:
                last_hash = h
                if config.CONTINUOUS_NARRATION:
                    _emit("VISION", narrate(png).replace("\n", " | "))
        except Exception as e:  # keep the thread alive through transient errors
            _emit("SYS", f"perception error: {e}")
        time.sleep(1.0 / config.FPS)


def start(background: bool = True) -> None:
    """Start the continuous perception thread once (idempotent)."""
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    _emit("SYS", "perception started - translating the screen continuously")
