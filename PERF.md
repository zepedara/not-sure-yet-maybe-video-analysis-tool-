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
- JPEG @896, VISION_WORKERS=2, OCR throttle 1.5s, num_predict=64
- **GPU Whisper** on the laptop 4070: large-v3-turbo, float16, ~64ms/1.2s chunk
  (was 141ms CPU). Enabled via nvidia-cublas/cudnn/cuda-runtime-cu12 wheels +
  DLL-dir setup in voice._add_cuda_dlls(); CPU/base auto-fallback kept.
- **bettercam (DXGI)** capture: ~0.5ms grab (vs mss ~13ms, 26x) and event-driven
  (only returns on real screen change); mss fallback kept. pHash still gates
  video/micro-changes.
- voice window 1.2s -> 1.0s (GPU makes compute negligible)

## Applied — GPU whisper + bettercam (this round)
Done and tested (see above).

## Ollama server env on ricksanchez — investigated, DELIBERATELY NOT CHANGED
rick already has `OLLAMA_FLASH_ATTENTION=1` + `OLLAMA_KV_CACHE_TYPE=q8_0`.
`OLLAMA_NUM_PARALLEL=1` is **intentional** (a comment in rick's systemd override
says it caps VRAM so the big REM models — qwen3.6:35b @23GB, rem-brain @18GB —
don't OOM the 4090). Raising it globally risks those. VISION per-request latency
is ~850ms regardless (model floor on the 4090); NUM_PARALLEL only helps burst
throughput. To get concurrent VISION safely, run a second vision node on l3e7's
3090 and round-robin (not yet done) rather than touching rick's global setting.

## Still deferred (optional)
1. **UIA fast-path for native apps** (uiautomation lib, run as admin): ~5-30ms
   exact text for WPF/WinForms/Office/Explorer. NOT reliable for terminals /
   Electron (VS Code) / browsers / games -> keep winocr as the universal path.
4. **bettercam** capture (DXGI, ~3x faster than mss, only emits on real change).
5. **NVIDIA Parakeet** instead of Whisper (English-only, faster + more accurate).
