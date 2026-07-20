"""Phase 2 voice — mic -> faster-whisper -> YOU lines.

Runs as its OWN PROCESS (python voice.py). CTranslate2's native libs segfault
if loaded in the same process as the screen pipeline (mss/PIL/tesseract), so we
isolate it: this process only does audio + whisper, and appends each transcript
to VOICE_OUT. The perception process tails that file and merges YOU lines into
the stream (see perception.spawn_and_tail / this module's spawn_and_tail()).
"""
from __future__ import annotations
import os
import sys
import time
import queue
import threading
import subprocess
from pathlib import Path

import numpy as np
import config

VOICE_OUT = Path(__file__).resolve().parent / "voice_lines.log"

def _add_cuda_dlls():
    """Put the pip-installed CUDA 12 DLLs (cublas/cudnn/cudart) on the loader path
    so faster-whisper can use the GPU on Windows. No-op if not present."""
    import os, glob, site
    try:
        sps = [p for p in site.getsitepackages() if "site-packages" in p]
        for sp in sps:
            for d in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
                os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
                try: os.add_dll_directory(d)
                except Exception: pass
    except Exception:
        pass



# ---- the isolated worker (runs when this file is executed directly) ----------
def _load_model():
    _add_cuda_dlls()
    from faster_whisper import WhisperModel
    cpu_model = getattr(config, "WHISPER_MODEL_CPU_FALLBACK", "base")
    tried = [(config.WHISPER_DEVICE, config.WHISPER_COMPUTE, config.WHISPER_MODEL)]
    if (config.WHISPER_DEVICE, config.WHISPER_COMPUTE) != ("cpu", "int8"):
        tried.append(("cpu", "int8", cpu_model))  # light model if GPU unavailable
    for dev, ct, model_name in tried:
        try:
            m = WhisperModel(model_name, device=dev, compute_type=ct)
            list(m.transcribe(np.zeros(config.SAMPLE_RATE, dtype=np.float32),
                              language="en")[0])  # force encode -> catch DLL errors
            _append(f"__READY__ whisper {model_name} on {dev}/{ct}")
            return m
        except Exception as e:
            _append(f"__INFO__ {dev}/{ct} {model_name} unusable: {str(e)[:50]}")
    raise RuntimeError("faster-whisper failed on all devices")


def _append(text: str) -> None:
    with VOICE_OUT.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def run() -> None:
    import sounddevice as sd
    model = _load_model()
    audio_q: queue.Queue = queue.Queue()

    def _cb(indata, frames, t, status):
        audio_q.put(indata[:, 0].copy())

    stream = sd.InputStream(samplerate=config.SAMPLE_RATE, channels=1,
                            dtype="float32", device=config.MIC_DEVICE, callback=_cb)
    stream.start()
    _append("__LISTENING__")
    window = int(config.SAMPLE_RATE * config.VOICE_WINDOW_SEC)
    buf = np.empty(0, dtype=np.float32)
    while True:
        buf = np.concatenate([buf, audio_q.get()])
        if len(buf) < window:
            continue
        chunk, buf = buf[:window], buf[window:]
        segs, _ = model.transcribe(chunk, language="en", beam_size=1,
                                   condition_on_previous_text=False,
                                   vad_filter=True,
                                   vad_parameters=dict(min_silence_duration_ms=500))
        text = " ".join(s.text.strip() for s in segs).strip()
        if text:
            _append(text)


# ---- used by the perception process: spawn this as a subprocess + tail it ----
def spawn_and_tail(emit) -> None:
    """Start voice.py as a separate process and feed its transcripts to `emit`."""
    if not config.AUDIO_ENABLED:
        return
    try:
        VOICE_OUT.write_text("", encoding="utf-8")  # truncate old lines
    except OSError:
        pass
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    emit("SYS", f"voice: started subprocess pid={proc.pid} (loading whisper…)")

    def _tail():
        pos = 0
        while True:
            try:
                if proc.poll() is not None:
                    emit("SYS", f"voice: subprocess exited ({proc.returncode})")
                    return
                with VOICE_OUT.open("r", encoding="utf-8") as f:
                    f.seek(pos)
                    new = f.readlines()
                    pos = f.tell()
                for ln in new:
                    ln = ln.strip()
                    if not ln:
                        continue
                    if ln.startswith("__READY__") or ln.startswith("__LISTENING__"):
                        emit("SYS", "voice: listening")
                    elif ln.startswith("__INFO__"):
                        emit("SYS", "voice: " + ln[8:].strip())
                    else:
                        emit("YOU", ln)
            except FileNotFoundError:
                pass
            time.sleep(0.5)

    threading.Thread(target=_tail, daemon=True).start()


if __name__ == "__main__":
    run()
