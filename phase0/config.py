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

# --- Decision 4: proactivity = SILENT -----------------------------------------
# Claude (Tier 2) speaks ONLY when you ask. No unprompted calls, no error-chime.
# NOTE: this governs Tier 2 (Claude) only. Tier 1 (local screen translation)
# still runs continuously below (CONTINUOUS_NARRATION) — that's free and local.
PROACTIVITY = "silent"        # one of: "silent", "hybrid", "continuous"

# --- Tier 1 behavior: translate everything, always (local, $0) ----------------
# Narrate every changed keyframe on rick's VLM into the timeline. This is the
# "looking at my screen, translating everything" layer. Costs only electricity.
CONTINUOUS_NARRATION = True

# --- Capture / narration tuning (levers) --------------------------------------
FPS = 1.0                     # sample rate (frames/sec)
HASH_DIFF_THRESHOLD = 6       # pHash hamming distance to count as a new keyframe
DOWNSCALE_WIDTH = 1280        # width sent to the VLM (cost/latency lever)
STREAM_WINDOW = 12            # recent timeline lines = the "ask Claude" payload

# --- Tier-1 narrator (local VLM on ricksanchez) -------------------------------
OLLAMA_HOST = "http://ricksanchez:11434"   # verified reachable from the laptop LAN
NARRATOR_MODEL = "moondream:latest"        # works on rick (ollama 0.31.2); llama3.2-vision needs newer ollama (mllama arch)

# --- Phase 1: OCR (exact on-screen text) --------------------------------------
# moondream describes the scene; tesseract captures literal strings (errors,
# paths, commands). Runs locally on the laptop where frames already live.
OCR_ENABLED = True
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows install
OCR_MAX_CHARS = 600           # truncate noisy full-screen OCR in the stream

# --- Phase 2: voice (mic -> faster-whisper, local) ----------------------------
# Your spoken questions/narration enter the same stream as YOU lines. Runs on
# the laptop's RTX 4070 (GPU verified). Highest-signal input = your intent.
AUDIO_ENABLED = True          # (overrides the Phase-0 placeholder above)
MIC_DEVICE = None             # None = system default (Arctis Nova Pro); or an index
WHISPER_MODEL = "base"        # base is fast+decent; "small"/"medium" = better/slower
WHISPER_DEVICE = "cpu"        # GPU needs cublas64_12.dll (not installed); cpu int8 is fast enough
WHISPER_COMPUTE = "int8"
VOICE_WINDOW_SEC = 4.0        # transcribe this much audio at a time
SAMPLE_RATE = 16000
