"""The agent reaches the corpus over a real MCP round-trip, not a file read.

Proves fidelity by comparing the MCP result to a direct corpus load — no
specific gap values are hardcoded, so nothing real leaks into the public tests.
"""

from __future__ import annotations

from learn_to_ship.corpus import load_gaps
from learn_to_ship.mcp_client import fetch_gaps


async def test_fetch_over_mcp_matches_direct_load():
    over_mcp = await fetch_gaps()
    direct = load_gaps()

    # Same gaps, same order, every field intact across the serialization round-trip.
    assert over_mcp == direct
    assert len(over_mcp) >= 4


async def test_round_trip_preserves_keywords_and_leverage():
    gaps = await fetch_gaps()
    top = max(gaps, key=lambda g: g.leverage)
    assert top.priority == 1
    assert top.keywords  # keywords survive the round-trip as a non-empty tuple
