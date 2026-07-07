# Deploy

The hosted agent ships as a small FastAPI container (`learn_to_ship/server.py` +
`Dockerfile`) exposing the **rank** graph only:

- `GET  /` — health check
- `POST /rank` — `{"candidates": [{id, title, tags}]}` → ranked list

(The v1 **recall** card-checker is not hosted — it needs your Anthropic key and
runs locally; see the README. So the deploy stays keyless and free.)

> **The hosted deploy serves the public stub, on purpose.** `.env` and the real
> corpus are `.dockerignore`'d, and the server never loads `.env`, so a container
> has no `LTS_CORPUS_PATH` and serves the fictional `data/jd-gaps.stub.yaml`. The
> private corpus stays on your machine (see README). Do not set `LTS_CORPUS_PATH`
> on a hosted deploy.

## Run the container locally (needs Docker)

```bash
docker build -t learn-to-ship .
docker run --rm -p 7860:7860 learn-to-ship
curl -s localhost:7860/ && curl -s -X POST localhost:7860/rank \
  -H 'content-type: application/json' \
  -d '{"candidates":[{"id":"a","title":"Deploy to a cloud container","tags":["cloud","deploy"]}]}'
```

## Option A — Hugging Face Spaces (free, recommended)

Free public Docker hosting with a shareable URL. No LangGraph Platform, no
subscription.

1. Create a **Docker** Space at <https://huggingface.co/new-space> (SDK: Docker,
   blank template). You get a git repo with a `README.md` (keep its frontmatter)
   and a starter `Dockerfile`.
2. Put this project's code in that Space repo — simplest is to point its
   `Dockerfile` at this public repo. Replace the Space's `Dockerfile` with:

   ```dockerfile
   FROM python:3.11-slim
   COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
   # git is needed to clone the repo at build time (the slim image has no git)
   RUN apt-get update && apt-get install -y --no-install-recommends git \
       && rm -rf /var/lib/apt/lists/*
   RUN useradd -m -u 1000 user
   USER user
   ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
   WORKDIR /home/user/app
   RUN git clone --depth 1 https://github.com/canglang-social/learn-to-ship.git .
   RUN uv sync --frozen --no-dev
   EXPOSE 7860
   CMD ["uv","run","--no-sync","uvicorn","learn_to_ship.server:app","--host","0.0.0.0","--port","7860"]
   ```

   (Or clone this repo into the Space and use the committed `Dockerfile` as-is.)
3. Commit → the Space builds and goes live at
   `https://<user>-learn-to-ship.hf.space`. Test:

   ```bash
   curl -s https://<user>-learn-to-ship.hf.space/
   ```

## Option B — Render / Fly.io / Railway (free-ish)

Any host that builds a Dockerfile works; the committed `Dockerfile` listens on
`7860` (override the port via the host's config if needed). Point the host at
this GitHub repo, or `docker push` the image to its registry.

## Option C — LangGraph Platform Cloud (paid)

Turnkey but **$39/mo** (LangSmith Plus; the free tier includes no deployments).
`langgraph.json` registers both graphs (`focus_director`, `card_reviewer`), so if
you later want the managed platform: connect this repo at
<https://smith.langchain.com> → Deployments. Free
self-hosted "Lite" (≤1M node-runs/yr) is also possible via the official
`langgraph build` image + a free LangSmith API key.
