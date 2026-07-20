# Performance / latency notes

Profiled + tuned 2026-07-19 (research-guided). Goal: "roughly instant" local
perception. Numbers measured on this fleet (laptop + ricksanchez RTX 4090).

## Latency profile — before -> after
| Path | Before | After | How |
|---|---|---|---|
| On-screen text (OCR) | tesseract 1.5-4s, garbled, **blocking** | **winocr ~330ms, clean, async** | winocr (Windows.Media.Ocr) primary; runs off-thread |
| Screen change -> VISION | 1.5-3s (OCR-blocked) | **~1s** | decoupled capture + parallel VISION workers |
| VISION quality | moondream: bboxes / echoes prompt = unusable | **qwen2.5vl:3b: accurate prose** | model swap |
| Speak -> text | up to ~4s | **~1.3s** | voice window 4.0s -> 1.2s (compute is only ~140ms) |
| Screen encode | PNG 79ms/257KB | **JPEG 3ms/60KB** | JPEG @896 |
| Model cold-reload stalls | multi-second | **none** | keep_alive=-1 + warmup |

## Architecture
Fast capture thread (6fps, cheap pHash) -> bounded queue -> N parallel VISION
workers (qwen2.5vl:3b, ~1s each) + async OCR worker (winocr, freshest-frame,
never blocks VISION). Voice runs as its own process. Latest-wins / drop-stale.

## Applied (in code)
- winocr OCR (tesseract fallback); qwen2.5vl:3b (moondream fallback)
- keep_alive=-1 (per-request; pins model, no server restart) + warmup
- narrator: num_predict=96, num_ctx=4096, temperature=0, top_k=1
- whisper: beam_size=1, condition_on_previous_text=False, vad min_silence=500ms
- JPEG @896, CAPTURE_FPS=6, VISION_WORKERS=2, OCR throttle 1.5s

## Deferred — optional manual steps (bigger wins, need care)
1. **Ollama server env on ricksanchez** (needs restarting ollama, which also
   serves other REM systems — do when rick is idle):
   `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0` (needs flash-attn),
   `OLLAMA_NUM_PARALLEL=2` (lets the 2 VISION workers run concurrently instead
   of serializing -> ~2x VISION throughput). Set in the systemd override, restart.
2. **GPU Whisper on the laptop** (CPU is 140ms so low priority):
   `pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"`, then
   `os.add_dll_directory(...)` for both wheels' bin dirs before importing
   faster_whisper; set WHISPER_DEVICE=cuda, model large-v3-turbo.
3. **UIA fast-path for native apps** (uiautomation lib, run as admin): ~5-30ms
   exact text for WPF/WinForms/Office/Explorer. NOT reliable for terminals /
   Electron (VS Code) / browsers / games -> keep winocr as the universal path.
4. **bettercam** capture (DXGI, ~3x faster than mss, only emits on real change).
5. **NVIDIA Parakeet** instead of Whisper (English-only, faster + more accurate).
