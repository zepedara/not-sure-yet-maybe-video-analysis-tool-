# MCP server — the "ask → Claude sees your screen → answers" loop

This is the Phase 3 core. It makes the interaction real: **Claude Code (on the
laptop) pulls your live screen context on demand** through MCP tools, and
answers your question. Proactivity stays **silent** — Claude only looks when you
ask; these tools are how it looks.

## What it does
On launch it starts the continuous local perception loop (`perception.py`):
full screen @1fps -> pHash change-detect -> rick's 4090 narrates each change ->
rolling stream + `../phase0/timeline.log`. Then it exposes two MCP tools:

| Tool | Use |
|---|---|
| `get_recent_context(lines=12)` | recent screen history — "what was I just doing / why is this failing" |
| `describe_screen_now()` | translate the current frame this instant — "look at my screen now" |

## Register with Claude Code (on the laptop)
```
pip install "mcp[cli]" mss Pillow imagehash requests
claude mcp add livestream -- python C:/path/to/mcp_server/server.py
```
Then just ask Claude Code normally: "why is my build failing?" — it calls
`get_recent_context`, reads the translated stream, and answers. Voice questions
join this same path once Phase 2 (Whisper on l3e7) lands.

## Notes
- Tier 1 runs on rick's local VLM (`moondream:latest`) — $0 marginal, nothing
  leaves the LAN. Claude (Tier 2) only sees the small TEXT stream, never images.
- Requires `ricksanchez` reachable with Ollama up (verified in the audit).
