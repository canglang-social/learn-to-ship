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
    assert card.front_en == "Why is retrieval separate from generation?"
    assert card.front_zh == "为什么检索与生成要分开？"
    assert card.back_en == "So each is measured on its own."
    assert card.back_zh == "这样各自可以单独度量。"
    assert (card.topic, card.subtopic, card.qtype) == (
        "rag",
        "rag/architecture".split("/")[1],
        "why",
    )


def test_a_clean_card_has_no_format_issues():
    (card,) = parse_cards(GOOD)
    assert lint_format(card) == []


def test_missing_chinese_is_flagged():
    text = "- English only question? #card #x #x/y #q/how\n\t- English only answer.\n"
    (card,) = parse_cards(text)
    kinds = {i.message for i in lint_format(card)}
    assert any("Chinese" in m for m in kinds)  # both front and back flagged
    assert all(i.kind == "format" for i in lint_format(card))


def test_bad_qtype_is_an_error():
    text = "- Q? 问？ #card #x #x/y #q/recall\n\t- A. 答。\n"
    (card,) = parse_cards(text)
    issues = lint_format(card)
    assert any(i.severity == "error" and "q/why" in i.message for i in issues)


def test_slash_delimiter_style_also_parses():
    text = "- Q? 问？ #card #x #x/y #q/how\n\t- English side. / 中文这边。\n"
    (card,) = parse_cards(text)
    assert card.back_en == "English side."
    assert card.back_zh == "中文这边。"
    assert lint_format(card) == []


def test_multiple_cards_parse_independently():
    cards = parse_cards(GOOD + GOOD)
    assert len(cards) == 2
