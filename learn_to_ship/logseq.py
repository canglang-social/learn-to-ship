"""Parse and format-lint human-authored Logseq #card blocks.

Pure and deterministic — no LLM, no I/O. This is the hermetic layer: it turns the
cards you wrote into `Card` structs and flags structural problems (missing
Chinese, wrong tag order, bad question-type). Content judgement — is the card one
atomic idea, is the answer correct — is the LLM checker's job (see recall.py).

Canonical card block (from the vault's own conventions):

    - <EN question?> <ZH question?> #card #<topic> #<topic>/<subtopic> #q/why
    \t- <EN answer.> <ZH answer.>
"""

from __future__ import annotations

import re

from .models import QTYPES, Card, CardIssue

# First run of CJK characters marks where the English half ends and Chinese begins.
_CJK = re.compile(r"[　-〿㐀-鿿＀-￯]")


def _split_bilingual(text: str) -> tuple[str, str]:
    """Split "English text 中文文本" into (en, zh).

    Accepts the vault's two styles: a plain space between halves (journal cards)
    or a ` / ` delimiter (topic-page cards). Returns ("", "") parts as empty when
    a half is absent, so the linter can flag it.
    """
    text = text.strip()
    if " / " in text:
        en, _, zh = text.partition(" / ")
        return en.strip(), zh.strip()
    m = _CJK.search(text)
    if not m:
        return text, ""  # no Chinese present
    return text[: m.start()].strip(), text[m.start() :].strip()


def _indent(line: str) -> int:
    return len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())


def _parse_tags(tag_str: str) -> tuple[str, str, str]:
    """From "#card #topic #topic/sub #q/why" → (topic, subtopic, qtype)."""
    topic = subtopic = qtype = ""
    for tag in tag_str.split():
        if not tag.startswith("#") or tag == "#card":
            continue
        body = tag[1:]
        if body.startswith("q/"):
            qtype = body[2:]
        elif "/" in body:
            subtopic = body.split("/", 1)[1]
            topic = topic or body.split("/", 1)[0]
        else:
            topic = topic or body
    return topic, subtopic, qtype


def parse_cards(text: str) -> list[Card]:
    """Parse every #card block in the text into Card structs."""
    lines = text.splitlines()
    cards: list[Card] = []
    for i, line in enumerate(lines):
        if "#card" not in line or not line.lstrip().startswith("-"):
            continue
        content = line.lstrip()[1:].strip()  # drop the leading "- "
        front_text, _, tag_str = content.partition("#card")
        topic, subtopic, qtype = _parse_tags("#card " + tag_str)
        front_en, front_zh = _split_bilingual(front_text)

        # Back = the first following, more-indented bullet.
        back_en = back_zh = ""
        for j in range(i + 1, len(lines)):
            nxt = lines[j]
            if not nxt.strip():
                continue
            if nxt.lstrip().startswith("-") and _indent(nxt) > _indent(line):
                back_en, back_zh = _split_bilingual(nxt.lstrip()[1:])
            break

        cards.append(
            Card(
                front_en=front_en,
                front_zh=front_zh,
                back_en=back_en,
                back_zh=back_zh,
                topic=topic,
                subtopic=subtopic,
                qtype=qtype,
                raw=line.strip(),
            )
        )
    return cards


def lint_format(card: Card) -> list[CardIssue]:
    """Deterministic format checks (no LLM). Returns issues, empty if clean."""
    issues: list[CardIssue] = []

    def err(msg: str) -> None:
        issues.append(CardIssue(kind="format", severity="error", message=msg))

    def warn(msg: str) -> None:
        issues.append(CardIssue(kind="format", severity="warn", message=msg))

    if not card.front_en:
        err("front is missing the English question")
    if not card.front_zh:
        err("front is missing the Chinese (中文) half")
    if not card.back_en:
        err("back is missing the English answer")
    if not card.back_zh:
        err("back is missing the Chinese (中文) half")
    if not card.topic:
        err("no topic tag (expected #card #<topic> #<topic>/<subtopic> #q/<type>)")
    if not card.subtopic:
        warn("no hierarchical sub-topic tag (#<topic>/<subtopic>)")
    if card.qtype not in QTYPES:
        err(f"question-type tag must be one of #q/why #q/how #q/apply (got #q/{card.qtype or '?'})")
    if card.front_en and "?" not in card.front_en:
        warn("front does not read as a question")

    return issues
