"""Desktop-livestream MCP server — lets Claude Code see your screen on demand.

Register once (one-time), then every Claude session can see your screen:
    claude mcp add livestream -- python <abs>/mcp_server/server.py

Screen-only by default (no mic) — you type questions to Claude, Claude looks.
Perception starts lazily on the first tool call, so merely having this registered
captures nothing until you actually ask Claude to look.
"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP

import perception
import config

config.AUDIO_ENABLED = False  # MCP path is screen-only; you type questions to Claude

mcp = FastMCP("livestream")
_ready = {"on": False}


def _ensure():
    if not _ready["on"]:
        perception.start()   # idempotent; screen VISION + OCR workers
        _ready["on"] = True


@mcp.tool()
def look_at_screen() -> str:
    """Capture and describe the user's CURRENT screen right now, in high fidelity.

    Use this whenever you need to see what's on the user's screen to help them —
    e.g. "what's on my screen?", "which button do I click?", "why is this
    erroring?", or when guiding them through a UI step by step. Returns a detailed
    description (buttons, panels, state) plus the exact on-screen text (OCR).
    """
    _ensure()
    return perception.snapshot_now()


@mcp.tool()
def get_recent_context(lines: int = 20) -> str:
    """Return the recent live stream of what's been on the user's screen.

    Use to answer "what was I just doing?" or to understand recent activity.
    Each line is timestamped: VISION = scene description, OCR = exact text.
    (Starts capturing on first use, so early calls may be short.)
    """
    _ensure()
    return perception.recent(lines)


if __name__ == "__main__":
    mcp.run()  # stdio
