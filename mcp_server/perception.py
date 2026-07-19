"""Shared Tier-1 perception core — LOW-LATENCY parallel design.

A fast capture thread samples the screen (cheap pHash change-detect) and feeds:
  - a queue of VISION workers (narrate each change on rick's VLM, ~400ms), and
  - an async OCR worker that always processes the FRESHEST frame (~1.5s, never
    blocks VISION).
Voice (Phase 2) runs as its own process. Everything merges into one rolling
stream + timeline.log. No hosted calls; nothing leaves the LAN.
"""
from __future__ import annotations
import io
import sys
import time
import queue
import threading
from pathlib import Path
from collections import deque
from datetime import datetime, timezone

import mss
import imagehash
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "phase0"))
import config              # noqa: E402
from narrator import narrate  # noqa: E402
import ocr                 # noqa: E402

TIMELINE = Path(__file__).resolve().parent.parent / "phase0" / "timeline.log"

_stream: deque[str] = deque(maxlen=500)
_lock = threading.Lock()
_started = False

# changed frames awaiting narration (bounded; drop oldest when workers are busy)
_frame_q: "queue.Queue[bytes]" = queue.Queue(maxsize=max(2, config.VISION_WORKERS * 2))
# freshest frame for OCR (OCR skips stale frames to stay current)
_latest = {"jpeg": None, "id": 0}
_latest_lock = threading.Lock()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _jpeg(img: Image.Image, w: int) -> bytes:
    if img.width > w:
        img = img.resize((w, int(img.height * w / img.width)))
    b = io.BytesIO()
    img.convert("RGB").save(b, format="JPEG", quality=config.JPEG_QUALITY)
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


def _capture_thread() -> None:
    """Sample fast, change-detect cheaply, hand changed frames to the workers."""
    last_hash = None
    fid = 0
    with mss.mss() as sct:
        mon = sct.monitors[config.MONITOR_INDEX]
        while True:
            shot = sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            h = imagehash.phash(img)
            if last_hash is None or (h - last_hash) >= config.HASH_DIFF_THRESHOLD:
                last_hash = h
                fid += 1
                jpeg = _jpeg(img, config.NARRATE_WIDTH)
                if config.OCR_ENABLED:
                    ocr_jpeg = _jpeg(img, config.OCR_WIDTH)
                    with _latest_lock:
                        _latest["jpeg"] = ocr_jpeg
                        _latest["id"] = fid
                try:
                    _frame_q.put_nowait(jpeg)
                except queue.Full:
                    pass  # workers busy; the freshest frame still reaches OCR
            time.sleep(1.0 / config.CAPTURE_FPS)


def _vision_worker() -> None:
    while True:
        jpeg = _frame_q.get()
        try:
            _emit("VISION", narrate(jpeg).replace("\n", " | "))
        except Exception as e:
            _emit("SYS", f"vision error: {e}")


def _ocr_worker() -> None:
    last_done = -1
    while True:
        with _latest_lock:
            fid, jpeg = _latest["id"], _latest["jpeg"]
        if jpeg is None or fid == last_done:
            time.sleep(0.2)
            continue
        last_done = fid
        try:
            t = ocr.ocr_png(jpeg)
            if t:
                _emit("OCR", t)
        except Exception as e:
            _emit("SYS", f"ocr error: {e}")
        time.sleep(config.OCR_MIN_INTERVAL)


def snapshot_now() -> str:
    """Capture + narrate the current frame immediately; return the narration."""
    with mss.mss() as sct:
        mon = sct.monitors[config.MONITOR_INDEX]
        shot = sct.grab(mon)
        img = Image.frombytes("RGB", shot.size, shot.rgb)
    text = narrate(_jpeg(img, config.NARRATE_WIDTH)).replace("\n", " | ")
    _emit("VISION", text + "  (on-demand)")
    if ocr.available():
        ot = ocr.ocr_png(_jpeg(img, config.OCR_WIDTH))
        if ot:
            _emit("OCR", ot)
    return text


def recent(lines: int = 12) -> str:
    """Return the last `lines` of the rolling translated stream as text."""
    with _lock:
        window = list(_stream)[-lines:]
    return "\n".join(window) if window else "(stream empty - perception just started)"


def start(background: bool = True) -> None:
    """Start capture + vision workers + OCR worker + voice (idempotent)."""
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_capture_thread, daemon=True).start()
    for _ in range(max(1, config.VISION_WORKERS)):
        threading.Thread(target=_vision_worker, daemon=True).start()
    if config.OCR_ENABLED and ocr.available():
        threading.Thread(target=_ocr_worker, daemon=True).start()
    _emit("SYS", "perception started - translating the screen continuously")
    if config.AUDIO_ENABLED:
        try:
            import voice
            voice.spawn_and_tail(_emit)  # separate process (avoids native segfault)
        except Exception as e:
            _emit("SYS", f"voice not started: {e}")
