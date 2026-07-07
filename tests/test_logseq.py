"""Deterministic parse + format-lint of Logseq #card blocks (hermetic, no LLM)."""

from __future__ import annotations

from learn_to_ship.logseq import lint_format, parse_cards

GOOD = (
    "- cards\n"
    "\t- Why is retrieval separate from generation? 为什么检索与生成要分开？ "
    "#card #rag #rag/architecture #q/why\n"
    "\t\t- So each is measured on its own. 这样各自可以单独度量。\n"
)


def test_parses_front_back_and_tags():
    (card,) = parse_cards(GOOD)
    assert card.front == "Why is retrieval separate from generation? 为什么检索与生成要分开？"
    assert card.back == "So each is measured on its own. 这样各自可以单独度量。"
    assert (card.topic, card.subtopic, card.qtype) == ("rag", "architecture", "why")


def test_a_clean_card_has_no_format_issues():
    (card,) = parse_cards(GOOD)
    assert lint_format(card) == []


def test_missing_chinese_is_flagged():
    text = "- English only question? #card #x #x/y #q/how\n\t- English only answer.\n"
    (card,) = parse_cards(text)
    issues = lint_format(card)
    assert any("Chinese" in i.message for i in issues)
    assert all(i.kind == "format" for i in issues)


def test_bad_qtype_is_an_error():
    text = "- Q? 问？ #card #x #x/y #q/recall\n\t- A. 答。\n"
    (card,) = parse_cards(text)
    assert any(i.severity == "error" and "q/why" in i.message for i in lint_format(card))


def test_multiple_cards_parse_independently():
    assert len(parse_cards(GOOD + GOOD)) == 2


# --- regression tests for the audit findings ---------------------------------


def test_inline_term_pairing_does_not_corrupt_the_card():
    # Vault convention: pair key terms inline as `term (中文)`. A split heuristic
    # would truncate the English at the first CJK char — we keep front whole.
    text = (
        "- What is the L2 norm (范数) of a vector? 什么是向量的 L2 范数？ "
        "#card #linear-algebra #linear-algebra/norms #q/what\n"
        "\t- The square root of the sum of squares. 各分量平方和的平方根。\n"
    )
    (card,) = parse_cards(text)
    assert "L2 norm (范数)" in card.front  # English half not cut at the first 汉字
    # (#q/what isn't a valid type — that's the only format issue, not a language one)
    assert not any("missing the English" in i.message for i in lint_format(card))
    assert not any("missing the Chinese" in i.message for i in lint_format(card))


def test_id_property_line_does_not_lose_the_back():
    # Real Logseq cards get an `id::` after first review; it sits between front
    # and back. The back must still be found.
    text = (
        "- Q? 问？ #card #x #x/y #q/why\n"
        "  id:: 6a310506-48b5-4405-879a-4b58e88abe47\n"
        "\t- The answer. 答案。\n"
    )
    (card,) = parse_cards(text)
    assert card.back == "The answer. 答案。"
    assert lint_format(card) == []


def test_card_group_is_not_parsed_as_a_card():
    text = "- [[ClozeTest]] #card-group\n\t- {{c1 something}} 一些东西\n"
    assert parse_cards(text) == []
