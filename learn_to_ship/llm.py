"""Choose the LLM behind the content seams (card checker, gap proposer).

DeepSeek first for cheap daily testing, Anthropic later — one env line, no
code change (QUESTIONS.md Q8):

    LTS_LLM_PROVIDER = auto (default) | deepseek | anthropic
      auto → deepseek if DEEPSEEK_API_KEY is set, else anthropic if
      ANTHROPIC_API_KEY is set, else no LLM (the seams degrade gracefully).
    LTS_LLM_MODEL = optional override of the per-provider default model.

Only this module knows provider names; recall.py and propose.py just ask for
"the chat model". The hermetic test suite never reaches this code's network
paths — the stubs replace the whole checker/proposer.
"""

from __future__ import annotations

import os

PROVIDER_ENV = "LTS_LLM_PROVIDER"
MODEL_ENV = "LTS_LLM_MODEL"

_KEY_ENVS = {"deepseek": "DEEPSEEK_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
_DEFAULT_MODELS = {"deepseek": "deepseek-chat", "anthropic": "claude-sonnet-5"}


def provider() -> str | None:
    """The configured provider, or None when no key is available."""
    choice = os.environ.get(PROVIDER_ENV, "auto").strip().lower()
    if choice in _KEY_ENVS:
        return choice
    for name, key_env in _KEY_ENVS.items():  # auto: deepseek first, by design
        if os.environ.get(key_env):
            return name
    return None


def has_llm_key() -> bool:
    """True when the selected provider's API key is present."""
    p = provider()
    return bool(p and os.environ.get(_KEY_ENVS[p]))


def model_name() -> str:
    return os.environ.get(MODEL_ENV) or _DEFAULT_MODELS.get(provider() or "", "")


def get_chat_model():
    """Build the configured chat model (lazy imports; needs a key at call time)."""
    p = provider()
    if p == "deepseek":
        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(model=model_name())
    if p == "anthropic":
        from langchain_anthropic import ChatAnthropic

        # Sonnet 5 rejects a non-default temperature, so none is set.
        return ChatAnthropic(model=model_name())
    raise ValueError(
        f"no LLM configured — set DEEPSEEK_API_KEY or ANTHROPIC_API_KEY (or {PROVIDER_ENV}) in .env"
    )
