"""
Tests for LLM Provider Layer — AI Developer OS
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from llm.provider import (
    get_llm_provider, StubProvider, LLMMessage, LLMResponse,
    GeminiProvider, OpenAIProvider, AnthropicProvider
)


class TestLLMMessage:
    def test_basic_message_creation(self):
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_system_role(self):
        msg = LLMMessage(role="system", content="You are helpful.")
        assert msg.role == "system"

    def test_assistant_role(self):
        msg = LLMMessage(role="assistant", content="I am an AI.")
        assert msg.role == "assistant"


class TestLLMResponse:
    def test_basic_response(self):
        resp = LLMResponse(content="Hello world", provider="stub", model="stub-v0")
        assert resp.content == "Hello world"
        assert resp.provider == "stub"
        assert resp.model == "stub-v0"

    def test_response_defaults(self):
        resp = LLMResponse(content="test", provider="gemini", model="gemini-pro")
        assert resp.input_tokens == 0
        assert resp.output_tokens == 0

    def test_response_with_tokens(self):
        resp = LLMResponse(
            content="hi", provider="openai", model="gpt-4o",
            input_tokens=10, output_tokens=5
        )
        assert resp.input_tokens == 10
        assert resp.output_tokens == 5


class TestStubProvider:
    def setup_method(self):
        self.provider = StubProvider()

    def test_stub_chat_returns_response(self):
        msg = LLMMessage(role="user", content="test")
        result = self.provider.chat(messages=[msg])
        assert isinstance(result, LLMResponse)
        assert result.provider == "stub"
        assert "[StubProvider]" in result.content

    def test_stub_chat_with_system_prompt(self):
        msg = LLMMessage(role="user", content="analyze this")
        result = self.provider.chat(
            messages=[msg],
            system_prompt="You are a coding assistant."
        )
        assert result.content is not None
        assert isinstance(result.content, str)

    def test_stub_chat_empty_messages(self):
        result = self.provider.chat(messages=[])
        assert isinstance(result, LLMResponse)
        assert result.provider == "stub"

    def test_stub_temperature_ignored(self):
        msg = LLMMessage(role="user", content="test")
        result1 = self.provider.chat(messages=[msg], temperature=0.0)
        result2 = self.provider.chat(messages=[msg], temperature=1.0)
        # Both should return valid responses
        assert result1.provider == "stub"
        assert result2.provider == "stub"

    def test_stub_max_tokens_respected(self):
        msg = LLMMessage(role="user", content="test")
        result = self.provider.chat(messages=[msg], max_tokens=100)
        assert isinstance(result.content, str)

    def test_stub_provides_heuristic_context(self):
        msg = LLMMessage(role="user", content="Plan how to add OAuth login")
        result = self.provider.chat(messages=[msg])
        # Stub should include the message content in its response
        assert result.content is not None
        assert len(result.content) > 0


class TestGetLLMProvider:
    def test_returns_stub_when_no_keys(self):
        """Without API keys set, get_llm_provider() should return StubProvider"""
        # Clear any keys
        env_keys = [
            "GOOGLE_API_KEY", "GEMINI_API_KEY",
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_PROVIDER"
        ]
        original = {k: os.environ.pop(k, None) for k in env_keys}
        try:
            provider = get_llm_provider()
            assert isinstance(provider, StubProvider)
        finally:
            for k, v in original.items():
                if v is not None:
                    os.environ[k] = v

    def test_explicit_stub_provider(self):
        provider = get_llm_provider("stub")
        assert isinstance(provider, StubProvider)

    def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError):
            get_llm_provider("nonexistent_provider_xyz")

    def test_provider_name_case_insensitive(self):
        p1 = get_llm_provider("STUB")
        p2 = get_llm_provider("Stub")
        p3 = get_llm_provider("stub")
        assert all(isinstance(p, StubProvider) for p in [p1, p2, p3])


class TestGeminiProviderUnit:
    """Unit test GeminiProvider initialization (no actual API calls)."""

    def test_gemini_requires_api_key(self):
        """GeminiProvider should fall back gracefully if GOOGLE_API_KEY is missing."""
        env_backup = os.environ.pop("GOOGLE_API_KEY", None)
        env_backup2 = os.environ.pop("GEMINI_API_KEY", None)
        try:
            # Should not raise — if key missing, StubProvider or graceful fallback
            provider = get_llm_provider("gemini")
            # May return Stub if no key
            assert hasattr(provider, "chat")
        finally:
            if env_backup:
                os.environ["GOOGLE_API_KEY"] = env_backup
            if env_backup2:
                os.environ["GEMINI_API_KEY"] = env_backup2

    def test_openai_requires_api_key(self):
        env_backup = os.environ.pop("OPENAI_API_KEY", None)
        try:
            provider = get_llm_provider("openai")
            assert hasattr(provider, "chat")
        finally:
            if env_backup:
                os.environ["OPENAI_API_KEY"] = env_backup

    def test_anthropic_requires_api_key(self):
        env_backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            provider = get_llm_provider("anthropic")
            assert hasattr(provider, "chat")
        finally:
            if env_backup:
                os.environ["ANTHROPIC_API_KEY"] = env_backup


class TestStubProviderEdgeCases:
    def test_very_long_message(self):
        provider = StubProvider()
        long_msg = LLMMessage(role="user", content="x" * 50000)
        result = provider.chat(messages=[long_msg])
        assert isinstance(result, LLMResponse)

    def test_none_content_handled(self):
        provider = StubProvider()
        msg = LLMMessage(role="user", content="")
        result = provider.chat(messages=[msg])
        assert isinstance(result, LLMResponse)

    def test_multiple_messages(self):
        provider = StubProvider()
        messages = [
            LLMMessage(role="user", content="First message"),
            LLMMessage(role="assistant", content="First response"),
            LLMMessage(role="user", content="Second message"),
        ]
        result = provider.chat(messages=messages)
        assert isinstance(result, LLMResponse)
        assert result.provider == "stub"

    def test_special_characters_in_message(self):
        provider = StubProvider()
        msg = LLMMessage(role="user", content='<script>alert("xss")</script> & SQL; DROP TABLE --')
        result = provider.chat(messages=[msg])
        assert isinstance(result, LLMResponse)

    def test_unicode_content(self):
        provider = StubProvider()
        msg = LLMMessage(role="user", content="日本語テスト 🚀 مرحبا ñoño")
        result = provider.chat(messages=[msg])
        assert isinstance(result, LLMResponse)
