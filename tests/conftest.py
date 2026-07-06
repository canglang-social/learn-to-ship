"""Shared test setup.

Pin every test to the committed public stub corpus, regardless of the developer's
environment. Without this, a shell that exports LTS_CORPUS_PATH (pointing at a
real/private corpus) would make the golden eval rank against different data and
fail — the eval must stay hermetic and deterministic.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _use_stub_corpus(monkeypatch):
    monkeypatch.delenv("LTS_CORPUS_PATH", raising=False)
