"""Phase 0 — capture loop skeleton (runs on the laptop = the watched machine).

Proves the end-to-end local path:
    screen @~1fps  ->  pHash change-detect (drop near-identical frames)
                   ->  cache keyframes to disk
                   ->  on hotkey (ENTER here in v0), narrate the last few
                       keyframes via ricksanchez's LOCAL VLM  ->  append to
                       timeline.log (the "stream").

No hosted API calls. Tier-2 (Claude Opus) is intentionally NOT wired here yet;
Phase 0's job is to validate capture -> local narration -> timeline.

Deps: see requirements.txt.  Run:  python capture_loop.py
Stop: Ctrl-C.  Trigger a narration: press ENTER in the terminal.
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

from narrator import narrate

FPS = 1.0                     # sample rate (frames/sec)
HASH_DIFF_THRESHOLD = 6       # hamming distance to count as a "new" keyframe
DOWNSCALE_WIDTH = 1280        # width sent to the VLM (cost/latency lever)
KEEP_LAST = 3                 # keyframes narrated per trigger
OUT = Path(__file__).parent / "keyframes"
TIMELINE = Path(__file__).parent / "timeline.log"
OUT.mkdir(exist_ok=True)

_recent: list[Path] = []      # most-recent keyframe paths
_lock = threading.Lock()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _downscaled_png(img: Image.Image, width: int) -> bytes:
    if img.width > width:
        h = int(img.height * width / img.width)
        img = img.resize((width, h))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _log(source: str, text: str) -> None:
    line = f"[{_ts()}] {source:<6} {text}"
    print(line, flush=True)
    with TIMELINE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def capture_thread() -> None:
    """Grab frames, keep only ones that differ enough from the last kept frame."""
    last_hash = None
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary display
        while True:
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            h = imagehash.phash(img)
            if last_hash is None or (h - last_hash) >= HASH_DIFF_THRESHOLD:
                last_hash = h
                name = OUT / f"kf_{datetime.now(timezone.utc):%H%M%S_%f}.png"
                name.write_bytes(_downscaled_png(img, DOWNSCALE_WIDTH))
                with _lock:
                    _recent.append(name)
                    del _recent[:-KEEP_LAST]
                _log("SCREEN", f"keyframe {name.name} (phash delta ok)")
            time.sleep(1.0 / FPS)


def trigger_loop() -> None:
    """v0 trigger = press ENTER. Later: global hotkey + error auto-detect."""
    _log("SYS", "ready — press ENTER to narrate the last keyframes (Ctrl-C to quit)")
    for _ in sys.stdin:
        with _lock:
            frames = list(_recent)
        if not frames:
            _log("SYS", "no keyframes captured yet")
            continue
        for p in frames:
            text = narrate(p.read_bytes())
            _log("VISION", f"{p.name}: {text}")


def main() -> None:
    t = threading.Thread(target=capture_thread, daemon=True)
    t.start()
    try:
        trigger_loop()
    except KeyboardInterrupt:
        _log("SYS", "shutting down")


if __name__ == "__main__":
    main()
