"""The JD-gap corpus parses and is internally consistent.

Assertions test the ranking *mechanics* on whatever corpus is loaded (the public
fictional demo by default), not any specific gap ranking — so no real career
conclusion is baked into the public tests.
"""

from __future__ import annotations

from learn_to_ship.corpus import load_gaps


def test_corpus_loads_and_is_nonempty():
    gaps = load_gaps()
    assert len(gaps) >= 4


def test_every_gap_is_well_formed():
    for g in load_gaps():
        assert g.id >= 1
        assert 0.0 <= g.freq <= 1.0
        assert 0.0 <= g.leverage <= 1.0
        assert g.keywords, f"gap {g.id} has no keywords to match on"


def test_highest_leverage_gap_is_priority_one():
    # Whatever the #1 gap is, it must carry the highest leverage so its study
    # items sort first. (Data-agnostic: no specific competency is asserted.)
    gaps = load_gaps()
    top = max(gaps, key=lambda g: g.leverage)
    assert top.priority == 1


def test_priority_and_leverage_agree():
    # Every ranked gap (priority set) outranks every non-gap by leverage.
    gaps = load_gaps()
    ranked = [g.leverage for g in gaps if g.priority is not None]
    unranked = [g.leverage for g in gaps if g.priority is None]
    if ranked and unranked:
        assert min(ranked) >= max(unranked)
