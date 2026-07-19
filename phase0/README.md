# Phase 0 — capture -> local narration -> timeline

Proves the concept end to end using **only local compute** (per `../AUDIT.md`):
the laptop captures its screen; `ricksanchez`'s RTX 4090 narrates keyframes via
Ollama; lines land in `timeline.log`. No hosted API calls.

## Locked decisions (see `config.py`)
| Decision | Choice |
|---|---|
| Watched machine | **laptop** (full screen, primary monitor) |
| Capture scope | **full-screen** |
| Audio | **mic-only** — wired in Phase 2 (`faster-whisper` on l3e7) |
| Proactivity | **hybrid** — ask-only in Phase 0; error-chime turns on with OCR (Phase 1) |

## Run (on the laptop)
```
pip install -r requirements.txt
python capture_loop.py          # Ctrl-C to stop; ENTER to narrate last keyframes
```
Prereqs: `ricksanchez` reachable with Ollama up and `llama3.2-vision:11b` pulled
(verified live in the audit; laptop reaches its Ollama directly over the LAN).
Override with `OLLAMA_HOST` / `NARRATOR_MODEL` env vars.

## What it does / doesn't
- **Does:** 1 fps full-screen capture, pHash change-detect, keyframe cache,
  local VLM narration on ENTER, append to `timeline.log`.
- **Doesn't yet:** OCR, Whisper/voice, Tier-2 Claude reasoning, MCP server,
  global hotkey. Those are Phase 1-3 (see `../AUDIT.md`).

## Why hybrid proactivity is "ask-only" for now
The error-chime needs a *cheap* per-frame signal so we don't run the VLM on
every frame (that's just continuous mode + cost). That signal is OCR
(`tesseract`), added in Phase 1. `config.ERROR_TRIGGERS` + `_has_error()` are
already in place; Phase 1 feeds OCR text through them to auto-chime.
