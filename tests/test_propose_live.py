"""Live Claude proposer — real API call. Marked `live`, skipped in CI (no key).

Run explicitly with:  uv run pytest -m live
"""

from __future__ import annotations

import os

import pytest

from learn_to_ship.models import Gap
from learn_to_ship.propose import ClaudeGapProposer

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY"),
]


def test_drafts_shippable_items_for_a_gap():
    gap = Gap(
        id=2,
        competency="Data engineering & analytics (SQL, warehousing, BI)",
        freq=0.55,
        level="partial",
        priority=2,
        leverage=0.8,
        keywords=("sql", "etl", "warehouse", "dbt"),
    )
    drafts = ClaudeGapProposer().propose(gap, ["Ship a Flutter app to the stores"])
    assert 2 <= len(drafts) <= 3
    for p in drafts:
        assert p.title and p.tags and p.route
        # Output-driven: not a "read about X" item.
        assert not p.title.lower().startswith(("read", "learn about"))
