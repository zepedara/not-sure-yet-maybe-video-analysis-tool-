# Desktop Livestream → Claude

Work at your desktop while local AI watches your screen + mic, translates
everything into a compact **text** stream, and lets Claude answer questions about
what you're doing — **fully local, ~$0 marginal** (Claude never sees images, only
small text). Silent by default: Claude speaks only when you ask.

## Status — working end to end

| Stream | How | Latency |
|---|---|---|
| **VISION** — screen described | `qwen2.5vl:3b` on ricksanchez's RTX 4090 (Ollama) | ~850ms |
| **OCR** — exact on-screen text | `winocr` (Windows.Media.Ocr), async | ~330ms |
| **YOU** — your voice | `faster-whisper large-v3-turbo` on the laptop GPU | ~1.1s speak→text |
| Screen capture | `bettercam` (DXGI), event-driven | ~0.5ms/grab |

All three merge into a rolling `phase0/timeline.log` that the **MCP server**
exposes to Claude Code on demand. See `PERF.md` for the full latency profile and
`AUDIT.md` for the fleet/role breakdown.

## Architecture (two tiers)

```
LAPTOP (watched + C2)                         ricksanchez (RTX 4090)
  bettercam capture ─┐                          qwen2.5vl:3b (VISION)
  pHash change-gate  ├─► parallel workers ──────► narrate
  winocr (OCR) ◄─────┘   (async, drop-stale)
  mic ─► faster-whisper (GPU, own process) ─► YOU
        └──────────► rolling text stream (timeline) ──► MCP ──► Claude (on ask)
```

- **Tier 1 — perception (local, always-on, free):** translate the screen + voice
  continuously into text.
- **Tier 2 — Claude (on ask only):** reads the recent stream, answers.

## Run it

**Live viewer** (watch the stream):
```
pip install -r phase0/requirements.txt
python run_live.py            # or double-click launch.bat
```
Requires ricksanchez reachable with Ollama up (`qwen2.5vl:3b` pulled) — the laptop
reaches it over the LAN. Screen + OCR start immediately; voice after ~10s (whisper
load). Ctrl-C to stop.

**As an MCP server** (Claude Code pulls your screen on ask):
```
claude mcp add livestream -- python <abs>/mcp_server/server.py
```
Then ask Claude Code "what's on my screen?" / "why is this failing?".

## Locked decisions
Watched machine = laptop · scope = full-screen · audio = mic-only · proactivity =
**silent** (Claude only speaks when asked). All in `phase0/config.py` (reversible).

## Layout
- `phase0/` — capture, narrator (VLM client), OCR, voice, config
- `mcp_server/` — perception core + FastMCP server
- `run_live.py` / `launch.bat` — live viewer
- `AUDIT.md` (fleet + roles) · `PERF.md` (latency) · `DESIGN.md` · `HANDOFF.md`
- `scripts/fleet_audit.{sh,ps1}` — hardware audit

## Requirements
Windows laptop (capture + voice), a LAN box with an NVIDIA GPU running Ollama, and
the models `qwen2.5vl:3b` (vision) + `winocr`/`faster-whisper` on the laptop.
GPU whisper on Windows needs the `nvidia-*-cu12` wheels (see `phase0/requirements.txt`).
