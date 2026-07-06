# Deploy

The agent is packaged for deployment as a hosted API. `langgraph.json` registers
the `focus_director` graph; `langgraph dockerfile` / `langgraph build` produce a
standard container image from it.

> **The hosted deploy runs the public stub, on purpose.** A cloud service must
> never hold the private career corpus. Do **not** set `LTS_CORPUS_PATH` in a
> hosted deploy — leave it unset so the endpoint serves the fictional
> `data/jd-gaps.stub.yaml`. The real corpus stays local (see README).

## Option A — LangGraph Platform (recommended)

No Docker needed locally; LangGraph Platform builds and hosts from the public
GitHub repo.

1. Go to <https://smith.langchain.com> → **Deployments** → **+ New Deployment**.
2. Connect GitHub and pick `canglang-social/learn-to-ship`, branch `main`.
3. It auto-detects `langgraph.json` (graph `focus_director`). Leave env vars
   empty (the stub is the default — no `LTS_CORPUS_PATH`).
4. **Submit** → wait for the build. You get a hosted API URL + an API key.

Smoke-test the live endpoint:

```bash
curl -s -X POST "$DEPLOY_URL/runs/wait" \
  -H "x-api-key: $LANGSMITH_API_KEY" \
  -H 'content-type: application/json' \
  -d '{"assistant_id":"focus_director","input":{"candidates":[
        {"id":"a","title":"Deploy to a cloud container","tags":["cloud","deploy"]}]}}'
```

## Option B — Container to a generic host (Fly.io / Render / Railway)

Needs Docker running locally.

```bash
# Build the image from langgraph.json
uv run langgraph build -t learn-to-ship

# Run it locally to verify (LangGraph API on :8000)
docker run --rm -p 8000:8000 learn-to-ship

# Then push to your host's registry and deploy per that host's docs, e.g. Fly:
#   fly launch --image learn-to-ship
```

The image serves the same `/runs/wait` API as Option A.

## Regenerate the Dockerfile

The `Dockerfile` is a generated artifact (gitignored). Regenerate any time:

```bash
uv run langgraph dockerfile Dockerfile
```
