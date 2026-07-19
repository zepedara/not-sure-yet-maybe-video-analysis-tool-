# Phase 0 — capture -> local narration -> timeline

Proves the concept end to end using **only local compute** (per `AUDIT.md`):
the laptop captures its screen; `ricksanchez`'s RTX 4090 narrates keyframes via
Ollama; lines land in `timeline.log`. No hosted API calls.

## Run (on the laptop)
```
pip install -r requirements.txt
python capture_loop.py          # Ctrl-C to stop; ENTER to narrate
```
Prereqs: `ricksanchez` reachable on the LAN with Ollama up and
`llama3.2-vision:11b` pulled (already installed per the audit). Override the
target with `OLLAMA_HOST=http://<node>:11434` and model with `NARRATOR_MODEL`.

## What it does / doesn't
- Does: 1 fps capture, pHash change-detect, keyframe cache, local VLM narration
  on ENTER, append to `timeline.log`.
- Doesn't yet: OCR, Whisper/voice, Tier-2 Claude reasoning, MCP server, global
  hotkey, error auto-trigger. Those are Phase 1-3 (see `AUDIT.md`).

## Note
`requests` reaches Ollama over HTTP on the LAN. If the fleet requires it, tunnel
via the existing SSH aliases instead of exposing 11434.
