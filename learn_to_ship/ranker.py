"""The deterministic ranking core of focus-director.

Pure function, no I/O: given candidate study items and the JD-gap corpus, decide
which gap each item unblocks and rank by closing-leverage. Kept separate from the
graph node so it is trivially unit-testable and provably deterministic — the same
inputs always yield the same ordering.
"""

from __future__ import annotations

import re
from functools import lru_cache

from .models import Gap, RankedItem, StudyItem


@lru_cache(maxsize=512)
def _kw_pattern(keyword: str) -> re.Pattern[str]:
    """Match a keyword only at a word start, open-ended at the tail.

    Anchoring the left edge to a non-alphanumeric boundary stops false positives
    like 'ci' matching inside 'tracing'; leaving the right edge open keeps stem
    tolerance so 'deploy' still matches 'deployment' and 'queue' matches 'queues'.
    """
    return re.compile(r"(?<![a-z0-9])" + re.escape(keyword))


def _match_gap(item: StudyItem, gaps: list[Gap]) -> tuple[Gap | None, int]:
    """Pick the single gap an item best unblocks.

    A gap matches when any of its keywords appears (word-start anchored) in the
    item's tags or title. Among matches we take the highest-leverage gap (that is
    the gap worth citing — the one whose closing does the most for the job hunt).
    Returns the gap and the number of keyword hits (used only for tie-breaking).
    """
    haystack = " ".join((*item.tags, item.title.lower()))
    best: Gap | None = None
    best_hits = 0
    for gap in gaps:
        hits = sum(1 for kw in gap.keywords if _kw_pattern(kw).search(haystack))
        if hits == 0:
            continue
        # Higher leverage wins; ties fall to the lower gap id for stability.
        if best is None or (gap.leverage, -gap.id) > (best.leverage, -best.id):
            best, best_hits = gap, hits
    return best, best_hits


def _rationale(item: StudyItem, gap: Gap | None) -> str:
    if gap is None:
        return "No JD gap matched — studying this unblocks nothing the corpus prices."
    pct = round(gap.freq * 100)
    if gap.priority is not None:
        stakes = f"gap #{gap.priority} to close"
    elif gap.leverage <= 0.05:
        stakes = "already a strength — low leverage"
    else:
        stakes = "not a top gap"
    return (
        f"Unblocks '{gap.competency}' ({stakes}; asked in ~{pct}% of JDs, you are '{gap.level}')."
    )


def rank(candidates: list[StudyItem], gaps: list[Gap]) -> list[RankedItem]:
    """Rank candidates by the leverage of the gap each one unblocks.

    Deterministic: sort key is (leverage desc, keyword-hits desc, gap freq desc,
    original index asc). The final index tie-break guarantees a stable, fully
    reproducible order even when two items are otherwise identical.
    """
    scored: list[tuple[float, int, float, int, RankedItem]] = []
    for idx, item in enumerate(candidates):
        gap, hits = _match_gap(item, gaps)
        score = gap.leverage if gap else 0.0
        freq = gap.freq if gap else 0.0
        ranked = RankedItem(
            item=item,
            score=score,
            gap=gap,
            rationale=_rationale(item, gap),
        )
        scored.append((score, hits, freq, idx, ranked))

    scored.sort(key=lambda t: (-t[0], -t[1], -t[2], t[3]))
    return [row[-1] for row in scored]
