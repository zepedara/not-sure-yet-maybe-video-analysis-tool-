"""Tier-1 narrator client — turns a keyframe into ~text using a LOCAL VLM.

Points at ricksanchez's Ollama (RTX 4090) by default. No hosted API, no cost,
nothing leaves the LAN. Falls back cleanly if the node is unreachable.
"""
from __future__ import annotations
import base64
import requests

# ricksanchez over the fleet LAN. Override with OLLAMA_HOST env if needed.
import os
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://ricksanchez:11434")
MODEL = os.environ.get("NARRATOR_MODEL", "llama3.2-vision:11b")  # moondream = lighter

PROMPT = (
    "You are a perception layer watching a developer's screen. In 2-3 terse "
    "lines, state: the active app/window, what the user appears to be doing, "
    "and any error text, dialog, or notable state. Be concrete. No preamble."
)


def narrate(png_bytes: bytes, timeout: float = 60.0) -> str:
    """Return a short textual narration of one keyframe, or an error marker."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": PROMPT, "images": [b64], "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except requests.RequestException as e:
        return f"[narrator unreachable: {e}]"


if __name__ == "__main__":
    import sys
    data = open(sys.argv[1], "rb").read()
    print(narrate(data))
