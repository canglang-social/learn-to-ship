"""The gap-proposer graph (QUESTIONS.md Q7, stage 2).

One node, `gap_proposer`: fetch the corpus over MCP, find the priority gaps
the candidate list leaves uncovered, and draft study-item proposals for each
via the injectable proposer. Compiled as `propose_graph` for langgraph.json.
Thin, like the other two graphs.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from . import propose
from .graph import _as_study_item
from .mcp_client import fetch_gaps
from .ranker import rank, uncovered


class ProposeState(TypedDict, total=False):
    candidates: Annotated[list, "existing study items, used for gap coverage"]
    proposals: Annotated[list[dict], "per-uncovered-gap drafted study items"]


async def gap_proposer(state: ProposeState) -> ProposeState:
    """Draft study items for every priority gap the candidates leave uncovered."""
    gaps = await fetch_gaps()
    candidates = [_as_study_item(c) for c in state.get("candidates", [])]
    missing = uncovered(rank(candidates, gaps), gaps)
    proposer = propose.get_proposer()  # module-level lookup so tests can monkeypatch
    existing = [c.title for c in candidates]

    blocks = []
    for gap in missing:
        drafts = proposer.propose(gap, existing)
        blocks.append(
            {
                "gap_id": gap.id,
                "priority": gap.priority,
                "competency": gap.competency,
                "freq": gap.freq,
                "level": gap.level,
                "proposals": [
                    {"title": p.title, "tags": list(p.tags), "route": p.route} for p in drafts
                ],
            }
        )
    return {"proposals": blocks}


def build_propose_graph():
    builder = StateGraph(ProposeState)
    builder.add_node("gap_proposer", gap_proposer)
    builder.add_edge(START, "gap_proposer")
    builder.add_edge("gap_proposer", END)
    return builder.compile()


propose_graph = build_propose_graph()
