"""Desktop-livestream MCP server (Phase 3 core).

Exposes the always-on local screen translation to Claude Code as tools it can
pull ON DEMAND. This is the "I ask a question -> Claude pulls screen context ->
answers" loop: proactivity stays SILENT (Claude only acts when you ask), and
these tools are how it sees your screen when you do.

Tier 1 (local VLM on rick) runs continuously in the background the moment this
server starts. Tier 2 = Claude Code itself, which calls these tools.

Run (registered in Claude Code, launched over stdio):
    python server.py
Or register:  claude mcp add livestream -- python /abs/path/to/server.py
"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP

import perception

mcp = FastMCP("livestream")

# start continuous screen translation as soon as the server loads
perception.start()


@mcp.tool()
def get_recent_context(lines: int = 12) -> str:
    """Return the most recent lines of the live screen-translation stream.

    Use this to answer questions about what the user is currently doing or was
    just doing on their screen ("why isn't this working", "what did I just run").
    Each line is timestamped: VISION = local narration of a screen change.

    Args:
        lines: how many recent stream lines to return (default 12).
    """
    return perception.recent(lines)


@mcp.tool()
def describe_screen_now() -> str:
    """Capture and translate the user's CURRENT screen right now, on demand.

    Use when you need the live state this instant rather than recent history —
    e.g. the user says "look at my screen" or "what's on screen now".
    """
    return perception.snapshot_now()


if __name__ == "__main__":
    mcp.run()  # stdio transport
