"""Phase 0 — continuous local translation + silent Claude (runs on the laptop).

Locked decisions (see config.py / AUDIT.md):
  watched = laptop   scope = full-screen   audio = mic-only (Phase 2)
  proactivity = SILENT -> Claude speaks only when you ask.

Two tiers, matching the intended model:
  TIER 1 (local, always-on, $0): full screen @~1fps -> pHash change-detect ->
    narrate EVERY changed keyframe on ricksanchez's VLM -> append to timeline.log.
    This is the "watch my screen and translate everything" layer.
  TIER 2 (Claude Opus, on ask only): NOT wired in Phase 0. Pressing ENTER shows
    the recent stream window -- exactly the payload the MCP server will hand to
    Claude when you ask a question. (Voice questions arrive here in Phase 2.)

Run:  pip install -r requirements.txt && python capture_loop.py
Stop: Ctrl-C.   Ask (preview the Claude payload): press ENTER.
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

import config
from narrator import narrate

OUT = Path(__file__).parent / "keyframes"
TIMELINE = Path(__file__).parent / "timeline.log"
OUT.mkdir(exist_ok=True)

# rolling in-memory view of the stream (the window an ask would send to Claude)
_stream: deque[str] = deque(maxlen=config.STREAM_WINDOW)
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
    with _lock:
        _stream.append(line)
    with TIMELINE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def capture_thread() -> None:
    """TIER 1: full-screen grab @FPS; narrate every changed frame (local, free)."""
    last_hash = None
    with mss.mss() as sct:
        monitor = sct.monitors[config.MONITOR_INDEX]  # full primary display
        while True:
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            h = imagehash.phash(img)
            if last_hash is None or (h - last_hash) >= config.HASH_DIFF_THRESHOLD:
                last_hash = h
                png = _downscaled_png(img, config.DOWNSCALE_WIDTH)
                name = OUT / f"kf_{datetime.now(timezone.utc):%H%M%S_%f}.png"
                name.write_bytes(png)
                if config.CONTINUOUS_NARRATION:
                    # translate everything, always -- this is the free local layer
                    _log("VISION", narrate(png).replace("\n", " | "))
                else:
                    _log("SCREEN", f"keyframe {name.name}")
            time.sleep(1.0 / config.FPS)


def ask_claude_preview() -> None:
    """SILENT Tier-2 stand-in: show the stream window an ask would send to Claude.

    In Phase 3 this becomes a real MCP call: the server exposes _stream, Claude
    pulls it + reasons. Here we just print it so the payload is visible.
    """
    with _lock:
        window = list(_stream)
    _log("SYS", f"--- you asked -> would send these {len(window)} lines to Claude ---")
    for ln in window:
        print("   " + ln, flush=True)
    _log("SYS", "--- (Tier-2 Claude call not wired in Phase 0) ---")


def input_loop() -> None:
    _log("SYS", f"proactivity={config.PROACTIVITY} (Claude speaks only when asked)")
    _log("SYS", f"scope={config.CAPTURE_SCOPE} audio={config.AUDIO_MODE}"
                f"(enabled={config.AUDIO_ENABLED}) continuous_narration="
                f"{config.CONTINUOUS_NARRATION}")
    _log("SYS", "Tier 1 translating your screen continuously. "
                "Press ENTER to ask Claude; Ctrl-C to quit.")
    for _ in sys.stdin:
        ask_claude_preview()


def main() -> None:
    threading.Thread(target=capture_thread, daemon=True).start()
    try:
        input_loop()
    except KeyboardInterrupt:
        _log("SYS", "shutting down")


if __name__ == "__main__":
    main()
