"""MCP client — how the agent reaches the JD-gap corpus.

The focus-director node calls `fetch_gaps` to obtain the corpus via a real MCP
round-trip (spawn the stdio server, initialize, call the tool, parse the result)
rather than reading the file. This is the seam the v0 spec cares about.
"""

from __future__ import annotations

import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .models import Gap

# Launch the server module in *this* interpreter so it shares the venv.
_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "learn_to_ship.mcp_server"],
    # Propagate the environment so an LTS_CORPUS_PATH override reaches the server.
    env=dict(os.environ),
)


async def fetch_gaps() -> list[Gap]:
    """Fetch the JD-gap corpus through the MCP `get_jd_gaps` tool."""
    async with stdio_client(_SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_jd_gaps", {})

    if result.isError:
        raise RuntimeError(f"get_jd_gaps failed: {result.content}")

    payload = _extract_text(result)
    return [Gap.from_dict(g) for g in json.loads(payload)]


def _extract_text(result) -> str:
    """Pull the JSON text out of an MCP tool result across SDK shapes."""
    for block in result.content:
        text = getattr(block, "text", None)
        if text is not None:
            return text
    raise RuntimeError(f"get_jd_gaps returned no text content: {result.content}")
