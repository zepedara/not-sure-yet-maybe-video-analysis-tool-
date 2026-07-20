"""Tier-1 narrator client — turns a keyframe into ~text using a LOCAL VLM.

Points at ricksanchez's Ollama (RTX 4090) by default (see config.py). No hosted
API, no cost, nothing leaves the LAN. Falls back cleanly if the node is down.
"""
from __future__ import annotations
import base64
import os
import requests

import config

OLLAMA_URL = os.environ.get("OLLAMA_HOST", config.OLLAMA_HOST)
MODEL = os.environ.get("NARRATOR_MODEL", config.NARRATOR_MODEL)

PROMPT = (
    "Describe what is on this screen in 2-3 plain sentences: the active "
    "app or window, what the user appears to be doing, and any visible error "
    "text or dialog. Write prose only - do not output coordinates or boxes."
)


def narrate(png_bytes: bytes, timeout: float = 60.0, model: str = None) -> str:
    """Return a short textual narration of one keyframe, or an error marker."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model or MODEL, "prompt": PROMPT, "images": [b64],
                  "stream": False, "keep_alive": getattr(config, "OLLAMA_KEEP_ALIVE", "30m"),
                  "options": {"num_predict": getattr(config, "NARRATE_MAX_TOKENS", 96),
                              "num_ctx": getattr(config, "NARRATE_CTX", 4096),
                              "temperature": 0, "top_k": 1}},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except requests.RequestException as e:
        return f"[narrator unreachable: {e}]"


if __name__ == "__main__":
    import sys
    print(narrate(open(sys.argv[1], "rb").read()))
