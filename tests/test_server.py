"""The FastAPI serving layer: front page, health, and the rank round-trip.

Hermetic — TestClient drives the real app in-process; ranking still does the
real MCP stdio round-trip against the stub corpus.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from learn_to_ship.server import app

client = TestClient(app)


def test_front_page_is_served_at_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/html")
    # The page must be self-contained: it calls the same-origin /rank API.
    assert "What should I study next?" in res.text
    assert '"/rank"' in res.text


def test_health_endpoint():
    assert client.get("/health").json() == {"status": "ok", "service": "focus-director"}


def test_rank_roundtrip_through_http():
    res = client.post(
        "/rank",
        json={"candidates": [{"id": "a", "title": "Ship a Flutter app", "tags": ["flutter"]}]},
    )
    (item,) = res.json()["ranked"]
    assert item["gap_priority"] == 1
    assert "Mobile" in item["rationale"]
