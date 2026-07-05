"""MCP server exposing the JD-gap corpus.

This is the ONE place that reads the corpus file. The agent consumes the corpus
only by calling this server's `get_jd_gaps` tool — closing the "consumes an MCP
tool" JD gap authentically (constraint: no direct file read in the agent).

Run standalone over stdio:  uv run python -m learn_to_ship.mcp_server
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from .corpus import load_gaps

mcp = FastMCP("learn-to-ship-jd-gaps", log_level="WARNING")


@mcp.tool()
def get_jd_gaps() -> str:
    """Return the JD-gap corpus as a JSON array.

    Each element is a competency clustered from logged JDs, with its JD frequency,
    Felix's current level, its gap-ranking priority, and the closing-leverage
    weight the focus-director ranks by.
    """
    gaps = load_gaps()
    return json.dumps([g.__dict__ | {"keywords": list(g.keywords)} for g in gaps])


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
