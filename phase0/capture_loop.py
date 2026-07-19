"""Phase 0 — capture loop (runs on the laptop = the watched machine).

Locked decisions (see config.py / AUDIT.md):
  watched machine = laptop   scope = full-screen
  audio = mic-only (Phase 2) proactivity = hybrid (ask + error-chime)

Flow (all local, no hosted calls):
    full screen @~1fps -> pHash change-detect -> cache keyframes
      -> narrate via ricksanchez's local VLM when:
           (a) you press ENTER (explicit ask), or
           (b) a narration/OCR line contains an error trigger (hybrid auto-chime)
      -> append every line to timeline.log (the "stream")

Tier-2 (Claude Opus reasoning) is intentionally NOT wired here yet.

Run:  pip install -r requirements.txt && python capture_loop.py
Stop: Ctrl-C.   Ask: press ENTER.
"""
from __future__ import annotations
import io
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timezone

import mss
import imagehash
from PIL import Image

import config
from narrator import narrate

OUT = Path(__file__).parent / "keyframes"
TIMELINE = Path(__file__).parent / "timeline.log"
OUT.mkdir(exist_ok=True)

_recent: list[Path] = []
_lock = threading.Lock()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _downscaled_png(img: Image.Image, width: int) -> bytes:
    if img.width > width:
        img = img.resize((width, int(img.height * width / img.width)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _log(source: str, text: str) -> None:
    line = f"[{_ts()}] {source:<6} {text}"
    print(line, flush=True)
    with TIMELINE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _has_error(text: str) -> bool:
    low = text.lower()
    return any(t in low for t in config.ERROR_TRIGGERS)


def _narrate_recent(reason: str) -> None:
    with _lock:
        frames = list(_recent)
    if not frames:
        _log("SYS", "no keyframes captured yet")
        return
    _log("SYS", f"narrating {len(frames)} keyframe(s) [{reason}]")
    for p in frames:
        text = narrate(p.read_bytes())
        _log("VISION", f"{p.name}: {text}")


def capture_thread() -> None:
    """Full-screen grab @FPS; keep only frames that differ enough (pHash).

    Hybrid proactivity: if a fresh keyframe's quick narration trips an error
    trigger, auto-narrate without waiting for ENTER.
    """
    last_hash = None
    with mss.mss() as sct:
        monitor = sct.monitors[config.MONITOR_INDEX]  # full primary display
        while True:
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            h = imagehash.phash(img)
            if last_hash is None or (h - last_hash) >= config.HASH_DIFF_THRESHOLD:
                last_hash = h
                name = OUT / f"kf_{datetime.now(timezone.utc):%H%M%S_%f}.png"
                name.write_bytes(_downscaled_png(img, config.DOWNSCALE_WIDTH))
                with _lock:
                    _recent.append(name)
                    del _recent[:-config.KEEP_LAST]
                _log("SCREEN", f"keyframe {name.name}")

                if config.PROACTIVITY == "continuous":
                    text = narrate(name.read_bytes())
                    _log("VISION", f"{name.name}: {text}")
                # NOTE: hybrid's error-chime needs a CHEAP per-frame signal so we
                # don't run the VLM on every frame (that would just be continuous
                # + costly). That signal is OCR (tesseract), added in Phase 1.
                # Until then, hybrid == ask-only. When OCR lands, replace this
                # with:  ocr_text = ocr(name); if _has_error(ocr_text): chime.
                elif config.PROACTIVITY == "hybrid":
                    pass  # ask-only in Phase 0; error-chime activates with OCR
            time.sleep(1.0 / config.FPS)


def trigger_loop() -> None:
    mode = config.PROACTIVITY
    _log("SYS", f"proactivity={mode} scope={config.CAPTURE_SCOPE} "
                f"audio={config.AUDIO_MODE}(enabled={config.AUDIO_ENABLED})")
    _log("SYS", "ready — press ENTER to ask; Ctrl-C to quit")
    for _ in sys.stdin:
        _narrate_recent("explicit ask")


def main() -> None:
    threading.Thread(target=capture_thread, daemon=True).start()
    try:
        trigger_loop()
    except KeyboardInterrupt:
        _log("SYS", "shutting down")


if __name__ == "__main__":
    main()
