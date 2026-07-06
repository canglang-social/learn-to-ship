# Container image for the focus-director FastAPI server.
# Serves the PUBLIC stub corpus (no LTS_CORPUS_PATH baked in — .env is
# .dockerignore'd). Listens on 7860, the Hugging Face Spaces default port.
#
# Build & run locally:
#   docker build -t learn-to-ship .
#   docker run --rm -p 7860:7860 learn-to-ship
FROM python:3.11-slim

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Hugging Face Spaces (and good practice) run as a non-root uid 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    UV_COMPILE_BYTECODE=1

WORKDIR /home/user/app
COPY --chown=user . /home/user/app

# Install the project + runtime deps (no dev group).
RUN uv sync --frozen --no-dev

EXPOSE 7860
CMD ["uv", "run", "--no-sync", "uvicorn", "learn_to_ship.server:app", \
     "--host", "0.0.0.0", "--port", "7860"]
