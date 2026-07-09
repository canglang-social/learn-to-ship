"""FastAPI serving layer for the focus-director graph.

A minimal HTTP wrapper so the agent runs as a free, self-hosted container (e.g.
Hugging Face Spaces) without the paid LangGraph Platform. This does not call
load_dotenv, so a deployed container has no LTS_CORPUS_PATH and serves the public
stub corpus — the private corpus never reaches a hosted service.

Human-facing pages (all styled by the shared theme in static/theme.css):
`GET /` — the demo front page (QUESTIONS.md Q4);
`GET /docs/{usage,development,learning-loop}` — the canonical docs/*.md rendered
as styled pages (Q5; the Markdown stays the source of truth). The JSON API is `POST /rank` + `GET /health`; FastAPI's
OpenAPI UI lives at /api-docs so /docs belongs to human readers.

Run locally:  uv run uvicorn learn_to_ship.server:app --port 7860
"""

from __future__ import annotations

from pathlib import Path

import markdown
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .graph import build_graph

app = FastAPI(title="learn-to-ship — focus-director", version="1.6.0", docs_url="/api-docs")

# Compile the graph once at startup and reuse across requests.
_graph = build_graph()

_STATIC = Path(__file__).parent / "static"

# Editable/source checkouts read the repo-root docs/; a non-editable install
# (the deploy container) reads the copy shipped inside the wheel (_docs — see
# pyproject force-include). Missing both is a packaging bug: fail loudly.
_PKG = Path(__file__).resolve().parent
_DOCS_DIR = next(d for d in (_PKG.parent / "docs", _PKG / "_docs") if d.is_dir())

app.mount("/static", StaticFiles(directory=_STATIC), name="static")

# Read the page once at startup; it is a single (near-)self-contained file.
_PAGE = (_STATIC / "index.html").read_text(encoding="utf-8")

# slug → (markdown source, page title)
_DOC_PAGES = {
    "usage": (_DOCS_DIR / "USAGE.md", "Usage guide"),
    "development": (_DOCS_DIR / "DEVELOPMENT.md", "Development guide"),
    "learning-loop": (_DOCS_DIR / "LEARNING-LOOP.md", "Learning loop"),
}

# Rewrite the docs' cross-links from GitHub-relative to served routes.
_LINK_MAP = {
    'href="USAGE.md"': 'href="/docs/usage"',
    'href="DEVELOPMENT.md"': 'href="/docs/development"',
    'href="LEARNING-LOOP.md"': 'href="/docs/learning-loop"',
}


def _render_doc(slug: str) -> str:
    """docs/*.md → a styled page. Mermaid blocks render client-side."""
    src, title = _DOC_PAGES[slug]
    body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    for old, new in _LINK_MAP.items():
        body = body.replace(old, new)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — learn-to-ship</title>
<link rel="stylesheet" href="/static/theme.css">
<link rel="stylesheet" href="/static/docs.css">
</head>
<body>
<main class="doc">
<p class="eyebrow"><a href="/">learn-to-ship</a> · docs · {title.lower()}</p>
{body}
<footer class="doc-footer">Rendered from
<a href="https://github.com/canglang-social/learn-to-ship/tree/main/docs">docs/ on GitHub</a>
— the Markdown is canonical.</footer>
</main>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  document.querySelectorAll("code.language-mermaid").forEach((code) => {{
    const div = document.createElement("div");
    div.className = "mermaid";
    div.textContent = code.textContent;
    code.closest("pre").replaceWith(div);
  }});
  // Drive the diagrams from the same design tokens as the page, so the
  // atlas is artifact-styled in both light and dark — not mermaid default.
  const css = getComputedStyle(document.documentElement);
  const v = (name) => css.getPropertyValue(name).trim();
  mermaid.initialize({{
    startOnLoad: false,
    theme: "base",
    themeVariables: {{
      fontFamily: v("--sans"),
      fontSize: "14.5px",
      primaryColor: v("--surface"),
      primaryTextColor: v("--ink"),
      primaryBorderColor: v("--accent"),
      lineColor: v("--muted"),
      secondaryColor: v("--code-bg"),
      tertiaryColor: v("--code-bg"),
      clusterBkg: v("--accent-soft"),
      clusterBorder: v("--line"),
      edgeLabelBackground: v("--code-bg"),
      background: v("--bg"),
    }},
  }});
  mermaid.run();
</script>
</body>
</html>"""


# Render once at startup — the files are baked into the image/checkout.
_RENDERED_DOCS = {slug: _render_doc(slug) for slug in _DOC_PAGES}


class Candidate(BaseModel):
    id: str
    title: str
    tags: list[str] = Field(default_factory=list)


class RankRequest(BaseModel):
    candidates: list[Candidate]


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """The demo front page — edit a study list, see it ranked with rationales."""
    return _PAGE


@app.get("/docs")
def docs_index() -> RedirectResponse:
    """/docs belongs to human readers (OpenAPI moved to /api-docs)."""
    return RedirectResponse("/docs/usage")


@app.get("/docs/{slug}", response_class=HTMLResponse)
def doc_page(slug: str) -> HTMLResponse:
    """A canonical docs/*.md file, rendered in the site style."""
    page = _RENDERED_DOCS.get(slug)
    if page is None:
        return HTMLResponse("Not found — try /docs/usage or /docs/development.", status_code=404)
    return HTMLResponse(page)


@app.get("/health")
def health() -> dict:
    """Liveness check (a 200 on `/` also satisfies host probes)."""
    return {"status": "ok", "service": "focus-director"}


@app.post("/rank")
async def rank(req: RankRequest) -> dict:
    """Rank a candidate study list by which JD gap each item unblocks."""
    candidates = [c.model_dump() for c in req.candidates]
    result = await _graph.ainvoke({"candidates": candidates})
    return {"ranked": result["ranked"], "uncovered": result.get("uncovered", [])}
