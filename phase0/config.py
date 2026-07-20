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
CAPTURE_FPS = 6.0             # how often we SAMPLE the screen for changes (cheap)
FPS = CAPTURE_FPS             # back-compat alias
HASH_DIFF_THRESHOLD = 6       # pHash hamming distance to count as a new keyframe
NARRATE_WIDTH = 896           # width sent to the VLM (JPEG); smaller = less network
JPEG_QUALITY = 80             # JPEG beats PNG ~25x on size+encode
DOWNSCALE_WIDTH = NARRATE_WIDTH  # back-compat alias
VISION_WORKERS = 2            # concurrent narration workers (hide the ~400ms each)
STREAM_WINDOW = 12            # recent timeline lines = the "ask Claude" payload
OLLAMA_KEEP_ALIVE = "10m"     # stay hot DURING a session, free rick VRAM ~10m after idle (respects other REM models)

# --- Tier-1 narrator (local VLM on ricksanchez) -------------------------------
OLLAMA_HOST = "http://ricksanchez:11434"   # verified reachable from the laptop LAN
NARRATOR_MODEL = "qwen2.5vl:3b"            # accurate scene understanding (~1s); moondream (274ms) echoes/emits bboxes = unusable

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
WHISPER_MODEL = "large-v3-turbo"  # GPU makes this fast + accurate; falls back to base
WHISPER_DEVICE = "cuda"       # GPU enabled via nvidia-cu12 wheels (see voice._add_cuda_dlls); ~64ms
WHISPER_COMPUTE = "float16"
VOICE_WINDOW_SEC = 1.0        # GPU transcribe ~64ms; window is the latency floor
SAMPLE_RATE = 16000

# --- OCR latency levers (added; async worker uses these) ----------------------
OCR_WIDTH = 1600              # OCR input width (accuracy vs speed); runs off-thread
OCR_MIN_INTERVAL = 1.5        # seconds between OCR passes (~1.5s each; async)

# --- narrator latency caps (research-guided) ----------------------------------
NARRATE_MAX_TOKENS = 64       # bound decode length -> bounds worst-case latency
NARRATE_CTX = 4096            # don't use ollama's 32k default (KV + prompt-eval scale)
WHISPER_MODEL_CPU_FALLBACK = "base"   # if GPU unavailable, use a light model on CPU

# --- capture backend ----------------------------------------------------------
USE_BETTERCAM = True          # DXGI capture: ~0.5ms grab (vs mss ~13ms), event-driven

# --- two-tier VLM: fast stream vs accurate on-demand -------------------------
# Continuous stream uses NARRATOR_MODEL (3b, fast). On-demand queries
# (describe_screen_now / the MCP "look now" tool) use the bigger, higher-fidelity
# model since accuracy matters more than speed when you actually ask.
ONDEMAND_MODEL = "qwen2.5vl:7b"   # better at buttons/icons/dense UI; ~slower
ONDEMAND_WIDTH = 1536             # higher res for on-demand fidelity

# --- VAD utterance capture (voice) --------------------------------------------
VAD_RMS_THRESHOLD = 0.012     # speech vs silence (adaptive noise floor on top)
VAD_HANGOVER_SEC = 0.6        # pause length that ends an utterance -> transcribe now
VAD_MIN_SPEECH_SEC = 0.35     # ignore blips shorter than this
VAD_MAX_UTT_SEC = 15.0        # force-flush very long utterances
