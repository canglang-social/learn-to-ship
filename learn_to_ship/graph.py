"""The LangGraph agent.

A thin graph with one meaningful node — focus-director. The node fetches the
JD-gap corpus over MCP, then ranks the candidate study list deterministically by
which gap each item unblocks. Compiled as `graph` for `langgraph.json`.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from .mcp_client import fetch_gaps
from .models import StudyItem
from .ranker import rank


class FocusState(TypedDict, total=False):
    """State flowing through the graph.

    `candidates` is the input study list (StudyItem objects, or plain dicts when
    the graph is invoked over the deployed HTTP API); `ranked` is the
    focus-director output as JSON-serializable dicts.
    """

    candidates: Annotated[list, "candidate study items to rank"]
    ranked: Annotated[list[dict], "study items ranked by gap leverage"]


def _as_study_item(c) -> StudyItem:
    """Accept either a StudyItem or a plain dict (from the HTTP API)."""
    return c if isinstance(c, StudyItem) else StudyItem.from_dict(c)


async def focus_director(state: FocusState) -> FocusState:
    """Rank the candidate study list by which JD gap each item unblocks.

    Reads the gap corpus via MCP (never a direct file read), then applies the
    deterministic ranker. This is the agent's one node. Output is plain dicts so
    the deployed endpoint returns clean JSON.
    """
    gaps = await fetch_gaps()
    candidates = [_as_study_item(c) for c in state.get("candidates", [])]
    ranked = rank(candidates, gaps)
    return {"ranked": [r.to_dict() for r in ranked]}


def build_graph():
    """Build and compile the focus-director graph."""
    builder = StateGraph(FocusState)
    builder.add_node("focus_director", focus_director)
    builder.add_edge(START, "focus_director")
    builder.add_edge("focus_director", END)
    return builder.compile()


# Module-level compiled graph — the deploy entrypoint (langgraph.json).
graph = build_graph()
