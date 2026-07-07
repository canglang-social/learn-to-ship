"""Parse and format-lint human-authored Logseq #card blocks.

Pure and deterministic — no LLM, no I/O. This is the hermetic layer: it turns the
cards you wrote into `Card` structs and flags structural problems (a missing
language, wrong tag order, bad question-type). Content judgement — is the card
one atomic idea, is the answer correct — is the LLM checker's job (see recall.py).

Canonical card block (from the vault's own conventions):

    - <EN question?> <中文问句？> #card #<topic> #<topic>/<subtopic> #q/why
    \t- <EN answer.> <中文答案。>
"""

from __future__ import annotations

import re

from .models import QTYPES, Card, CardIssue

# `#card` as a whole tag — not the `#card-group` prefix (cloze/image groups).
_CARD_TAG = re.compile(r"(?<!\S)#card(?!\S)")
# Presence tests, so we never have to split the bilingual text into halves.
_LATIN = re.compile(r"[A-Za-z]")
_CJK = re.compile(r"[　-〿㐀-鿿＀-￯]")  # common Han + CJK/fullwidth punctuation
# A Logseq block property line, e.g. "  id:: <uuid>" — skip it when finding the back.
_PROPERTY = re.compile(r"^\s*\S[\w-]*:: ")


def _indent(line: str) -> int:
    e = line.expandtabs(4)
    return len(e) - len(e.lstrip())


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
            head, sub = body.split("/", 1)
            subtopic = sub
            topic = topic or head
        else:
            topic = topic or body
    return topic, subtopic, qtype


def parse_cards(text: str) -> list[Card]:
    """Parse every #card block in the text into Card structs."""
    lines = text.splitlines()
    cards: list[Card] = []
    for i, line in enumerate(lines):
        m = _CARD_TAG.search(line)
        if not m or not line.lstrip().startswith("-"):
            continue
        content = line.lstrip()[1:]  # drop the leading "- "
        tag_start = _CARD_TAG.search(content)
        front = content[: tag_start.start()].strip()
        topic, subtopic, qtype = _parse_tags(content[tag_start.start() :])

        # Back = the first following, more-indented bullet, skipping blank lines
        # and property lines (id::, deck::) that Logseq stores between the two.
        back = ""
        for nxt in lines[i + 1 :]:
            if not nxt.strip() or _PROPERTY.match(nxt):
                continue
            if nxt.lstrip().startswith("-") and _indent(nxt) > _indent(line):
                back = nxt.lstrip()[1:].strip()
            break

        cards.append(
            Card(
                front=front,
                back=back,
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

    if not card.front:
        err("front is empty")
    else:
        if not _LATIN.search(card.front):
            err("front is missing the English question")
        if not _CJK.search(card.front):
            err("front is missing the Chinese (中文) half")
        if "?" not in card.front and "？" not in card.front:
            warn("front does not read as a question")

    if not card.back:
        err("back is missing (no indented answer bullet under the front)")
    else:
        if not _LATIN.search(card.back):
            err("back is missing the English answer")
        if not _CJK.search(card.back):
            err("back is missing the Chinese (中文) half")

    if not card.topic:
        err("no topic tag (expected #card #<topic> #<topic>/<subtopic> #q/<type>)")
    if not card.subtopic:
        warn("no hierarchical sub-topic tag (#<topic>/<subtopic>)")
    if card.qtype not in QTYPES:
        err(f"question-type tag must be one of #q/why #q/how #q/apply (got #q/{card.qtype or '?'})")

    return issues
