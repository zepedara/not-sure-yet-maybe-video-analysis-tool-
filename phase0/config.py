"""Phase 0 configuration — locked decisions (2026-07-19).

All four are user-confirmed and cheap to reverse (plain values here).
See AUDIT.md for the reasoning behind each.
"""

# --- Decision 1: watched machine = the laptop ---------------------------------
# Capture runs locally on DOMMYMOMMY; no remote capture agent.
WATCHED_MACHINE = "laptop"

# --- Decision 3: capture scope = full-screen ----------------------------------
# "monitor" = mss monitor index (1 = primary). Switch to "window"/"region" later.
CAPTURE_SCOPE = "full-screen"
MONITOR_INDEX = 1
# REGION = {"top": 0, "left": 0, "width": 1920, "height": 1080}  # if scope=="region"

# --- Decision 2: audio = mic-only ---------------------------------------------
# Phase 0 does not capture audio yet; this flags intent for Phase 2 (Whisper on l3e7).
AUDIO_MODE = "mic-only"       # one of: "mic-only", "mic+system", "none"
AUDIO_ENABLED = False         # Phase 2 flips this on

# --- Decision 4: proactivity = hybrid (ask + error-chime) ---------------------
# Silent until hotkey/ask, but auto-narrate when an error string is detected.
PROACTIVITY = "hybrid"        # one of: "hybrid", "silent", "continuous"
# Substrings that trigger an auto-narration when found in OCR/narration text.
ERROR_TRIGGERS = [
    "error", "traceback", "exception", "failed", "fatal",
    "cannot", "not found", "denied", "refused", "undefined",
    "segmentation fault", "panic", "unhandled",
]

# --- Capture / narration tuning (levers) --------------------------------------
FPS = 1.0                     # sample rate (frames/sec)
HASH_DIFF_THRESHOLD = 6       # pHash hamming distance to count as a new keyframe
DOWNSCALE_WIDTH = 1280        # width sent to the VLM (cost/latency lever)
KEEP_LAST = 3                 # keyframes narrated per trigger

# --- Tier-1 narrator (local VLM on ricksanchez) -------------------------------
OLLAMA_HOST = "http://ricksanchez:11434"   # verified reachable from the laptop LAN
NARRATOR_MODEL = "llama3.2-vision:11b"      # moondream:latest = lighter fallback
