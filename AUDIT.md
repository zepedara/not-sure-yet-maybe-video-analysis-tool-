# FLEET AUDIT — results & role assignment

> This closes the "ACTION NEEDED" step in `HANDOFF.md`. The audit was run
> live on all real nodes on 2026-07-19 (laptop + `ricksanchez` via SSH +
> `l3e7` via SSH). Roles are assigned below. **Headline: Tier 1 can be
> fully local today — no hosted narrator needed.**

## Nodes

### DOMMYMOMMY — the laptop (C2 + the watched machine)
- **CPU:** AMD Ryzen AI 9 HX 370 — 12C / 24T (+ XDNA2 NPU, ~50 TOPS)
- **RAM:** 31 GB
- **GPU:** NVIDIA RTX 4070 Laptop **8 GB** (+ Radeon 890M iGPU)
- **OS:** Windows 11 Pro for Workstations (build 26100)
- **Tooling:** Python 3.12, ffmpeg present; ollama / tesseract / docker missing

### ricksanchez — heavy perception (Tier-1 VLM narrator)
- **CPU:** AMD Ryzen Threadripper 3960X — 24C / 48T
- **RAM:** 125 GB
- **GPU:** NVIDIA **RTX 4090 24 GB**
- **OS:** Ubuntu (kernel 6.8, x86_64)
- **Tooling:** Ollama 0.31.2, Docker 29.1.3, Python 3.12, ffmpeg present; tesseract missing
- **Already-installed Ollama models that match the design:**
  - `llama3.2-vision:11b` (7.8 GB) — vision narrator
  - `moondream:latest` (1.7 GB) — lightweight vision narrator
  - `qwen2.5:32b`, `qwen3.6:35b`, `gemma3:27b`, `qwen2.5-coder:32b` — reasoning/backups
  - `nomic-embed-text` — embeddings; `rem-voice`, `rem-brain` — existing REM models

### l3e7 — always-on perception #2
- **CPU:** Intel i9-11900K — 8C / 16T
- **RAM:** 64 GB
- **GPU:** NVIDIA **RTX 3090 24 GB** (+ Intel UHD 750 iGPU)
- **OS:** Windows 11 Pro
- **Tooling:** Ollama, Docker, Python, ffmpeg, nvidia-smi all present; tesseract missing
- **Ollama models:** `qwen3:14b`, `gemma2:9b`, `qwen2.5:7b`, `nomic-embed-text`
- Note: also runs Plex — has spare GPU headroom but is not idle-dedicated.

> The HANDOFF listed four nodes (`l3`, `echo 7`, `Rick Sanchez`, laptop). The
> real fleet is **three machines**: the laptop, `ricksanchez`, and `l3e7`
> (which covers both "l3" and "echo 7"). Roles below reflect the three.

## Role assignment

| Role | Node | Why |
|---|---|---|
| **C2** — Claude Code, MCP server, timeline store, screen capture of the work | **laptop** | It's the machine being watched; orchestration is light. |
| **Heavy VLM narrator** — keyframe -> structured event text | **ricksanchez** | Biggest GPU (4090/24 GB), models already installed, huge RAM. |
| **Whisper (voice->text) + OCR + change-detect assist** | **l3e7** | Second 24 GB GPU; keeps rick free for VLM; already has ffmpeg. |

Perception is embarrassingly parallel, so if rick saturates, l3e7's 3090 can
run a second `llama3.2-vision`/`moondream` instance and split keyframes by
round-robin.

## Decisions the audit resolves

- **Open-question #1 (privacy / locality) -> FULLY LOCAL.** rick already runs
  `llama3.2-vision:11b` and `moondream` on a 4090; l3e7 has a spare 3090. The
  design's reason to start on hosted Haiku ("local is more setup") no longer
  applies — the setup is already done. Tier 1 = local Ollama VLM = **$0
  marginal + nothing leaves the LAN**. Haiku 4.5 stays as an optional
  quality-fallback only.
- **Tier 2 stays Claude Opus 4.8** (reasoning on trigger) — unchanged.
- **Whisper:** `faster-whisper` on l3e7's 3090 (local, $0). Feasible.
- **OCR:** `tesseract` is **missing on every node** — must be installed on
  whichever node runs OCR (l3e7). This is the one net-new install required.

## Still needs a human decision (not answerable from hardware)

These are DESIGN section 7 questions the audit can't settle — they're preferences:
2. **OS target of the watched screen** — assumed the **laptop (Windows)**.
3. **System audio vs mic-only** — which to capture?
4. **Full-screen vs a chosen window/region?**
5. **How proactive** — silent-until-asked, or allowed to interrupt on errors?

## Concrete next steps (revised from HANDOFF, now unblocked)

1. Run fleet audit -> assign roles: **DONE (this file)**.
2. **Phase 0 skeleton** — see `phase0/`: screen capture @1fps + pHash
   change-detect on the laptop -> cache keyframes -> on hotkey, narrate the
   last keyframes via **rick's local `llama3.2-vision`** (proves the local
   Tier-1 path end to end) and print. No hosted calls required.
3. Wire the narrated lines into a rolling `timeline.log` (the "stream").
4. Add `faster-whisper` on l3e7 for voice; add `tesseract` for exact OCR.
5. Expose the timeline as an MCP server the laptop's Claude Code pulls on demand.
