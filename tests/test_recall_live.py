"""Live Claude check — real API call. Marked `live`, skipped in CI (no key).

Run explicitly with:  ANTHROPIC_API_KEY=… uv run pytest -m live
"""

from __future__ import annotations

import os

import pytest

from learn_to_ship.logseq import parse_cards
from learn_to_ship.recall import ClaudeCardChecker

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY"),
]


def test_flags_a_planted_factual_error():
    # Deliberately wrong: HF Spaces default port is 7860, not 8080.
    text = "- What port do HF Spaces default to? HF Spaces 默认端口是多少？ #card #deploy #deploy/hf #q/how\n\t- 8080. 端口 8080。\n"
    (card,) = parse_cards(text)
    material = "Hugging Face Spaces (Docker) serve on port 7860 by default."
    issues = ClaudeCardChecker().check(card, material)
    assert any(i.kind == "correctness" for i in issues), issues


def test_flags_a_compound_card():
    text = (
        "- What is RAG and how does reranking and chunking and hybrid search each work? "
        "什么是 RAG，重排、分块、混合检索各自如何工作？ #card #rag #rag/overview #q/how\n"
        "\t- RAG retrieves then generates; reranking reorders; chunking splits; hybrid mixes "
        "BM25 and vectors. RAG 先检索后生成；重排重新排序；分块切分；混合结合 BM25 与向量。\n"
    )
    (card,) = parse_cards(text)
    issues = ClaudeCardChecker().check(card, None)
    assert any(i.kind == "complexity" for i in issues), issues
