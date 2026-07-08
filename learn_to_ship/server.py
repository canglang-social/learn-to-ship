"""FastAPI serving layer for the focus-director graph.

A minimal HTTP wrapper so the agent runs as a free, self-hosted container (e.g.
Hugging Face Spaces) without the paid LangGraph Platform. This does not call
load_dotenv, so a deployed container has no LTS_CORPUS_PATH and serves the public
stub corpus — the private corpus never reaches a hosted service.

`GET /` serves the demo front page (one static file, no build toolchain, no
persistence — scoped in spec.md via QUESTIONS.md Q4); the JSON API is
`POST /rank`, and health moved to `GET /health`.

Run locally:  uv run uvicorn learn_to_ship.server:app --port 7860
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .graph import build_graph

app = FastAPI(title="learn-to-ship — focus-director", version="1.2.0")

# Compile the graph once at startup and reuse across requests.
_graph = build_graph()

# Read the page once at startup; it is a single self-contained file.
_PAGE = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


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


@app.get("/health")
def health() -> dict:
    """Liveness check (a 200 on `/` also satisfies host probes)."""
    return {"status": "ok", "service": "focus-director"}


@app.post("/rank")
async def rank(req: RankRequest) -> dict:
    """Rank a candidate study list by which JD gap each item unblocks."""
    candidates = [c.model_dump() for c in req.candidates]
    result = await _graph.ainvoke({"candidates": candidates})
    return {"ranked": result["ranked"]}
