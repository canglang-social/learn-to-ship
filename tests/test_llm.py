"""Provider selection for the LLM seams (Q8): DeepSeek first, Anthropic later."""

from __future__ import annotations

import pytest

from learn_to_ship import llm


@pytest.fixture(autouse=True)
def _clean_llm_env(monkeypatch):
    for var in ("DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", llm.PROVIDER_ENV, llm.MODEL_ENV):
        monkeypatch.delenv(var, raising=False)


def test_no_keys_means_no_provider():
    assert llm.provider() is None
    assert not llm.has_llm_key()


def test_auto_prefers_deepseek_when_its_key_is_set(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert llm.provider() == "deepseek"  # "test cheap first" is the default
    assert llm.model_name() == "deepseek-chat"
    assert llm.has_llm_key()


def test_auto_falls_back_to_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert llm.provider() == "anthropic"
    assert llm.model_name() == "claude-sonnet-5"


def test_explicit_provider_wins_over_auto(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv(llm.PROVIDER_ENV, "anthropic")
    assert llm.provider() == "anthropic"
    assert llm.model_name() == "claude-sonnet-5"


def test_explicit_provider_without_its_key_has_no_llm(monkeypatch):
    monkeypatch.setenv(llm.PROVIDER_ENV, "deepseek")
    assert llm.provider() == "deepseek"
    assert not llm.has_llm_key()  # selected, but unusable — seams degrade


def test_model_override(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv(llm.MODEL_ENV, "deepseek-reasoner")
    assert llm.model_name() == "deepseek-reasoner"


def test_get_chat_model_builds_the_deepseek_client(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    model = llm.get_chat_model()
    assert type(model).__name__ == "ChatDeepSeek"


def test_get_chat_model_without_config_is_loud():
    with pytest.raises(ValueError, match="no LLM configured"):
        llm.get_chat_model()
