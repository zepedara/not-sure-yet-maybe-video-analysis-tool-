# Phase 0 — continuous local translation + silent Claude

Proves the model end to end using **only local compute** (per `../AUDIT.md`):
the laptop watches its own screen and **rick's RTX 4090 translates every changed
frame to text** (Tier 1, always-on, $0). Claude (Tier 2) stays silent until you
ask. Lines land in `timeline.log` — the rolling "stream."

## Locked decisions (see `config.py`)
| Decision | Choice |
|---|---|
| Watched machine | **laptop** (full screen, primary monitor) |
| Capture scope | **full-screen** |
| Audio | **mic-only** — wired in Phase 2 (`faster-whisper` on l3e7) |
| Proactivity | **silent** — Claude speaks only when you ask; no unprompted calls |

## The two tiers
- **Tier 1 (local, always-on, free):** screen -> pHash change-detect -> VLM
  narrates *every* changed frame into the timeline. "Translate everything."
- **Tier 2 (Claude Opus, on ask only):** not wired in Phase 0. Pressing ENTER
  prints the recent stream window — the exact payload the MCP server will hand
  to Claude when you ask. Voice questions arrive here in Phase 2.

## Run (on the laptop)
```
pip install -r requirements.txt
python capture_loop.py          # Ctrl-C to stop; ENTER to preview an "ask"
```
Prereqs: `ricksanchez` reachable with Ollama up and `llama3.2-vision:11b` pulled
(verified live; laptop reaches its Ollama over the LAN). Override with
`OLLAMA_HOST` / `NARRATOR_MODEL` env vars. `moondream:latest` is a lighter model
if continuous narration loads the 4090 too much.

## What it does / doesn't
- **Does:** continuous full-screen capture + local translation into the stream;
  ENTER previews the Claude-bound payload.
- **Doesn't yet:** Whisper/voice (Phase 2), real Tier-2 Claude call + MCP server
  (Phase 3), OCR for exact strings (Phase 1). See `../AUDIT.md` for the roadmap.
