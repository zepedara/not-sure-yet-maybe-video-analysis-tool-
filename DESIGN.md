# Desktop Livestream → Claude: Architecture & Build Plan

> Status: planning. No application code yet — this document is the blueprint.
> Goal: let me (the user) do something on my desktop while Claude watches a
> live-ish stream of what's happening, understands it, and guides me in real
> time via a terminal/side chat.

## 1. The core reality that shapes everything

No LLM ingests raw video. Claude (and every current model) reads **images** and
**text**. So a "livestream to Claude" is really: *continuously sample the screen
+ audio, distill it into a compact text/event stream, and feed that to Claude.*

We embrace this with a **two-tier design**:

- **Tier 1 — Perception (fast, always-on, cheap):** watches the raw video/audio
  densely and emits a running stream of *what is happening* (a narration + events
  + on-screen text). This is the "video analyzed by an LLM, then translated into a
  stream" layer.
- **Tier 2 — Reasoning (Claude Opus 4.8, on meaningful moments):** consumes the
  distilled stream (plus select keyframes) and produces *guidance* — what to do
  next, warnings, better approaches.

Tier 1 is the bridge. Tier 2 is the coach. Splitting them keeps cost sane and
latency low, because we only invoke the expensive reasoning model when something
worth reasoning about has happened.

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                            YOUR DESKTOP (live)                           │
 └───────────────┬───────────────────────┬─────────────────────────────────┘
                 │ screen (1–2 fps)       │ mic + system audio
                 ▼                        ▼
        ┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
        │ Frame sampler    │     │ Audio capture    │     │ OCR (per     │
        │ (mss / ffmpeg)   │     │ (sounddevice)    │     │ keyframe)    │
        │ + change detect  │     │                  │     │ Tesseract    │
        └────────┬─────────┘     └────────┬─────────┘     └──────┬───────┘
                 │ keyframes              │ audio chunks         │ text
                 ▼                        ▼                      │
        ┌──────────────────┐     ┌──────────────────┐           │
        │ TIER 1: Vision   │     │ Speech→text      │           │
        │ narrator (fast   │     │ (Whisper)        │           │
        │ VLM, e.g. Haiku) │     │                  │           │
        │ → event stream   │     │ → transcript     │           │
        └────────┬─────────┘     └────────┬─────────┘           │
                 │                        │                      │
                 └──────────┬─────────────┴──────────────────────┘
                            ▼
                 ┌─────────────────────────┐
                 │ CONTEXT STREAM (merged   │   a single time-ordered log:
                 │ timeline: events +       │   [t] narration / [t] you said… /
                 │ transcript + OCR + tags) │   [t] OCR: "error: ..." / keyframe refs
                 └────────────┬────────────┘
                              │ on trigger (change burst / hotkey / question)
                              ▼
                 ┌─────────────────────────┐
                 │ TIER 2: Claude Opus 4.8 │   reads the recent stream window +
                 │ (vision + reasoning)    │   1–3 keyframes → guidance
                 └────────────┬────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │ OUTPUT: terminal / side │
                 │ chat  (later: notif/TTS)│
                 └─────────────────────────┘
```

## 2. Components in detail

### 2.1 Frame sampler (Tier 1 input)
- Capture the screen at **1–2 fps** (tunable). Full 30fps is unnecessary and
  unaffordable for LLM analysis.
- **Change detection**: perceptual hash / frame diff. Drop near-identical frames
  so the narrator only processes meaningful changes. A "keyframe" = a frame that
  differs enough from the last one.
- Downscale before sending upstream (cost scales with resolution). Keep full-res
  keyframes cached locally in case Tier 2 wants to look closely.
- Tooling: `mss` (fast cross-platform screen grab) or `ffmpeg` for capture;
  `imagehash`/`Pillow` for diffing.

### 2.2 Vision narrator (Tier 1 core — "video → stream")
The always-on model that converts keyframes into a **textual event stream**. It
maintains short rolling context ("last thing I saw was the terminal; now a browser
opened") and emits structured lines like:

```
[00:41] app=Terminal  action="ran `npm test`"  note="3 tests failing"
[00:47] app=VSCode     action="editing config.py, near line 40"
[00:52] alert          text="Traceback: KeyError 'db_host'"
```

Model choices for this tier (cost/latency sensitive — it runs constantly):
- **Cheapest hosted:** Claude Haiku 4.5 (fast, multimodal, $1/$5 per 1M tokens).
- **Local option:** a small local vision-language model (e.g. a quantized VLM) if
  you want zero per-frame API cost and full privacy — more setup, weaker output.
- Recommendation: start with **Haiku 4.5** for quality/simplicity; add a local
  fallback later if cost or privacy demands it.

### 2.3 Audio pipeline
- Capture **mic** (your voice / intent) and optionally **system audio**.
- Transcribe with **Whisper** — `faster-whisper` locally (private, no per-minute
  cost) or the hosted API. Chunk on silence boundaries so lines land in the
  timeline promptly.
- Your voice is the highest-signal input: "I'm trying to get the DB connection
  working" tells me your *intent*, which screen frames alone can't.

### 2.4 OCR layer
- Run **Tesseract** on keyframes (or a cropped region of interest) to pull exact
  on-screen text — error messages, file paths, command output, values.
- Why, if the vision model can already read frames? Because OCR is cheap,
  deterministic, and exact — great for capturing precise strings (stack traces,
  URLs, numbers) that a narration might paraphrase or miss. It complements, not
  replaces, the vision narrator.

### 2.5 Context stream (the merge point)
All three sources write into **one time-ordered timeline** — the single artifact
that represents "what's going on." Each entry is timestamped and tagged by source
(`vision` / `voice` / `ocr`), with references to cached keyframe image files. This
timeline is:
- the compact "stream" that gets sent to Tier 2,
- append-only and windowed (keep last N minutes hot; summarize/roll off older).

### 2.6 Reasoning layer (Tier 2 — Claude Opus 4.8)
- On a trigger, send Claude: a **window of the recent timeline** + **1–3 relevant
  keyframes** (so I can look at the actual screen, not just the narration) + a
  system prompt defining me as a hands-on coach.
- Uses **prompt caching** on the stable system prompt + rolling context so repeated
  calls are cheap.
- Returns concise, actionable guidance ("your KeyError is because `.env` isn't
  loaded before `config.py` imports — move the `load_dotenv()` call above line 3").

### 2.7 Triggering (when Tier 2 fires)
Per your pick, start with a lightweight mix:
- **Change burst:** a flurry of new events after quiet → likely a good moment.
- **Explicit ask:** hotkey or "Claude, what now?" (highest signal, cheapest).
- **Error detected:** OCR/narrator flags an error string → proactively chime in.
- Continuous "coach every N seconds" is available but off by default (noisy/pricey).

### 2.8 Output
- **v1:** terminal / side-chat pane. Simplest, fastest to build.
- **later:** desktop notifications, or text-to-speech for hands-free coaching.

## 3. Data flow summary

1. Sampler grabs frames @1–2fps → change detector keeps keyframes.
2. Keyframes → vision narrator → event lines; keyframes also → OCR → text lines.
3. Mic → Whisper → transcript lines.
4. All lines merged into the timeline (the "stream").
5. Trigger fires → recent timeline window + keyframes → Claude Opus 4.8.
6. Guidance → terminal/side chat.

## 4. Cost model (rough, tune later)

- **Tier 1 (Haiku 4.5)** dominates volume. A downscaled keyframe ≈ ~1k tokens.
  At ~1 keyframe/sec of *active* work that's the main spend; change-detection and
  idle gaps cut it substantially. Ballpark: cents to low dollars per active hour.
- **Tier 2 (Opus 4.8)** fires rarely (on triggers) with cached context — a few
  cents per invocation.
- **Whisper local** = $0 marginal. **OCR local** = $0 marginal.
- Biggest levers: sampling rate, downscale resolution, change-detection
  aggressiveness, and how often Tier 2 fires.

## 5. Phased build plan

**Phase 0 — Loop skeleton (proves the concept)**
- Screen capture @1fps + change detection → cache keyframes.
- Hotkey → send last few keyframes straight to Opus 4.8 → print guidance.
- No Tier 1 narrator yet, no audio. Validates capture → Claude → output end to end.

**Phase 1 — Tier 1 narrator + timeline**
- Add the fast vision narrator (Haiku) producing the event stream.
- Add OCR on keyframes.
- Build the merged timeline; Tier 2 now consumes the timeline + keyframes.

**Phase 2 — Voice**
- Add mic capture + Whisper transcript into the timeline.
- Intent-aware guidance ("you said you're trying to X…").

**Phase 3 — Smart triggering + polish**
- Change-burst and error-detection triggers; prompt caching; windowing/summarizing
  the timeline; rate limits and cost guards.

**Phase 4 — UX**
- Notifications / TTS / an overlay or small desktop app if wanted.

## 6. Proposed stack

- **Language:** Python (best ecosystem: `mss`, `faster-whisper`, `pytesseract`,
  `anthropic` SDK). TS/Electron is the path if this later becomes a GUI app.
- **Screen:** `mss` (+ `Pillow`/`imagehash` for diffing).
- **Audio:** `sounddevice` + `faster-whisper`.
- **OCR:** `pytesseract` (Tesseract).
- **LLMs:** `claude-haiku-4-5` (Tier 1), `claude-opus-4-8` (Tier 2), via the
  official `anthropic` SDK with prompt caching.

## 7. Open questions / decisions to make before Phase 1

1. **Privacy / locality:** OK sending screenshots to a hosted model (Haiku), or do
   you want Tier 1 fully local (a local VLM) so nothing leaves the machine?
2. **OS target:** which desktop (macOS / Windows / Linux)? Affects capture, audio,
   and hotkey libraries.
3. **System audio vs mic only:** do you want it to hear app audio too, or just you?
4. **Full-screen vs a chosen window/region:** watch everything, or a focused area?
5. **How proactive:** silent until asked, or allowed to interrupt when it spots an
   error?

Once those are answered, Phase 0 is a short, self-contained build.
```