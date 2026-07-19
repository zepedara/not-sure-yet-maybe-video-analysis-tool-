# HANDOFF — Desktop Livestream → Claude (read this first)

> Written from a phone session to hand off to a laptop Claude Code session.
> Everything decided so far is here. Companion files: `DESIGN.md` (full
> architecture) and `scripts/fleet_audit.sh` (hardware audit).
> Branch: `claude/desktop-livestream-integration-34iquf`.

## The idea (one paragraph)

Let me work on my desktop while an AI watches a live-ish stream of what I'm
doing and coaches me in real time. No LLM ingests raw video — so **local models
on my own hardware do all the heavy perception** (read the screen, identify UI
objects, OCR the text, transcribe my voice) and **compile it into a single
rolling terminal-based text document**. That compact text stream — plus my
narration — is fed to Claude (Claude Code / Opus), which does the reasoning and
guidance. I keep working in parallel; Claude pulls the latest context when it
needs it.

## Why this is cheap (the cost insight)

The expensive part of "AI watches your screen" is **images** (~1.6k–4.8k tokens
each). In this design **Claude never sees images** — a local model turns each
frame into ~150 words of text. So:
- Continuous watching = **$0 marginal** (runs on our hardware, just electricity).
- Claude only reads small text, only on turns where guidance is wanted = pennies.

This flips it from "$X/hour of image tokens" to "our own GPUs + occasional cheap
text reasoning."

## Architecture (two tiers)

```
DESKTOP (live)
  screen @1–2fps ─┐        mic/audio ─┐
                  ▼                    ▼
  TIER 1 — PERCEPTION (LOCAL, on the fleet, always-on, cheap)
    • frame sampler + change-detect (pHash)      → keyframes only
    • UI/object parser (OmniParser / Florence-2) → structured elements
    • OCR (Tesseract / PaddleOCR)                → exact on-screen text
    • vision narrator (Ollama: qwen2.5-vl /       → "you're in VS Code, terminal
      llama3.2-vision / moondream)                  shows ModuleNotFoundError"
    • speech→text (faster-whisper)               → my narration transcript
        └── all merged into ──►  CONTEXT STREAM  (one rolling terminal doc)
                                       │  (on trigger / on demand)
  TIER 2 — REASONING (Claude Code / Opus 4.8)
    reads the recent stream window (text) → guidance → terminal
```

Example of the rolling context doc (this is the "stream"):
```
[12:03:15] SCREEN  VS Code — editing app.py; terminal: "ModuleNotFoundError: No module named 'requests'"
[12:03:15] OCR     pip install requests
[12:03:15] UI      [button "Run"] [tab "app.py"] [panel "TERMINAL"]
[12:03:18] YOU     "why isn't my import working"
```

## Decisions locked in

- **Locality: HYBRID.** Local models do the constant work (OCR, Whisper, dedup,
  UI parsing) on the fleet. Only reach for cheap **Haiku 4.5** on the occasional
  frame where local narration quality isn't enough.
- **Feed method: MCP server.** The local tool exposes "current screen state" as
  something Claude Code pulls on demand — best for working in parallel.
- **Output: terminal / side chat** (v1). Later: notifications / text-to-speech.
- **Triggering (start simple):** hotkey / "Claude, what now?" + error-detected
  proactive chime-in. Continuous coach off by default (noisy/pricey).

## Fleet / hardware plan

Framing: the **laptop is C2** (command node) — runs Claude Code, the MCP server,
orchestration, and holds the merged stream doc. The beefier nodes do GPU-heavy
perception. Perception is embarrassingly parallel, so distributing it is ideal.

**ACTION NEEDED — audit each node.** On `l3`, `echo 7`, `Rick Sanchez`, and the
laptop, run:
```bash
git pull
bash scripts/fleet_audit.sh > audit_<node>.txt
```
Then give the outputs to Claude. Role assignment logic:
| What the audit shows            | Role                                             |
|---------------------------------|--------------------------------------------------|
| Biggest GPU / most VRAM         | Heavy VLM narrator (Qwen2.5-VL / OmniParser)      |
| Modest GPU or fast CPU          | Always-on: Whisper + OCR + change-detection       |
| The laptop                      | C2: Claude Code + MCP server + orchestration      |
| RAM / disk / `ollama` present   | What we can run today vs. needs setup            |

> NOTE: A phone/cloud Claude session **cannot** see the fleet — the audit must be
> run on each real machine and the text handed back. (The Claude Code cloud
> sandbox is a 4-core Xeon, 15GB RAM, no GPU — controller-only, not our hardware.)

## Prior art (what to reuse instead of building from scratch)

| Tool | License | Use |
|---|---|---|
| **ScreenMind** (github.com/ayushh0110/ScreenMind) | **MIT** | **Fork as Tier-1 base.** Its pipeline (capture → pHash dedup → OCR → vision model → structured JSON → SQLite) ≈ our perception layer. Missing piece = the real-time coaching loop, which we add. |
| **screenshot_based_ai_desktop_assistant** (github.com/KatavinaNguyen/...) | MIT | ~100-line Phase-0 starter: hotkey → OCR → LLM (Claude) → popup. |
| **screenpipe** (github.com/screenpipe/screenpipe) | source-available, non-commercial | Mature 24/7 capture + MCP server; use as a *data source*, not a fork. |
| **OmniParser** (Microsoft) | open | The "object identifier" — screenshot → structured UI elements. |

**Recommendation:** fork **ScreenMind** for Tier 1 (MIT, modular, already local),
bolt on the Tier-2 Claude reasoning loop + triggering + MCP output.

## Next steps (in order)

1. Run `fleet_audit.sh` on all 4 nodes; hand outputs to Claude → assign roles.
2. Pull ScreenMind into the repo; study `analyzer.py` / `capture/` / `dedup.py`.
3. Phase 0: hotkey → keyframes → text stream → Claude Code, end to end.
4. Phase 1: add OmniParser + OCR + local narrator → the rolling context doc.
5. Phase 2: add Whisper (voice). Phase 3: MCP server + smart triggering.

## How to continue on the laptop

```bash
git fetch origin
git checkout claude/desktop-livestream-integration-34iquf
git pull
# then open Claude Code here and point it at HANDOFF.md + DESIGN.md
```
