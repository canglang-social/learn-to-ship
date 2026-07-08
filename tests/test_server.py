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
    body = res.json()
    (item,) = body["ranked"]
    assert item["gap_priority"] == 1
    assert "Mobile" in item["rationale"]
    # Coverage (Q7): one candidate covers gap #1, so priority gaps 2–5 are
    # uncovered — the API names the silence instead of hiding it.
    assert [g["priority"] for g in body["uncovered"]] == [2, 3, 4, 5]


def test_styled_docs_pages_render_the_markdown():
    for slug, marker in (("usage", "The atlas"), ("development", "Architecture map")):
        res = client.get(f"/docs/{slug}")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/html")
        assert marker in res.text
        # Mermaid blocks survive as fenced code for the client-side renderer.
        assert "language-mermaid" in res.text


def test_docs_cross_links_point_at_routes_not_files():
    res = client.get("/docs/usage")
    assert 'href="/docs/development"' in res.text
    assert 'href="DEVELOPMENT.md"' not in res.text


def test_docs_index_redirects_to_usage():
    res = client.get("/docs", follow_redirects=False)
    assert res.status_code in (302, 307)
    assert res.headers["location"] == "/docs/usage"


def test_unknown_doc_is_404():
    assert client.get("/docs/nope").status_code == 404


def test_shared_theme_is_served_and_linked():
    assert client.get("/static/theme.css").status_code == 200
    for path in ("/", "/docs/usage"):
        assert 'href="/static/theme.css"' in client.get(path).text
