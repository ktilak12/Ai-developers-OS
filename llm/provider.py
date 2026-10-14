"""
Unified LLM Provider — AI Developer OS
Supports Google Gemini, OpenAI, and Anthropic Claude with a single interface.

Usage:
    from llm.provider import get_llm_provider

    llm = get_llm_provider()          # reads LLM_PROVIDER env var
    response = llm.chat([
        {"role": "system", "content": "You are a helpful agent."},
        {"role": "user", "content": "What should I do?"}
    ])
    print(response.content)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class LLMMessage:
    role: str          # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"
    raw: Optional[Any] = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class LLMProvider:
    """Abstract base; concrete subclasses override chat()."""

    def chat(
        self,
        messages: List[LLMMessage | Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        raise NotImplementedError

    # Convenience: accepts dicts or LLMMessage objects
    @staticmethod
    def _coerce(messages: List[LLMMessage | Dict[str, str]]) -> List[LLMMessage]:
        out: List[LLMMessage] = []
        for m in messages:
            if isinstance(m, LLMMessage):
                out.append(m)
            else:
                out.append(LLMMessage(role=m["role"], content=m["content"]))
        return out


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    """
    Uses the google-generativeai SDK.
    Required env: GEMINI_API_KEY
    Optional env: GEMINI_MODEL (default: gemini-1.5-pro-latest)
    """

    def __init__(self):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        genai.configure(api_key=api_key)
        self._genai = genai
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

    def chat(
        self,
        messages: List[LLMMessage | Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        msgs = self._coerce(messages)

        # Extract optional system message
        sys_parts: List[str] = []
        if system_prompt:
            sys_parts.append(system_prompt)

        gemini_history = []
        user_final = None

        for msg in msgs:
            if msg.role == "system":
                sys_parts.append(msg.content)
            elif msg.role == "user":
                user_final = msg.content
                if gemini_history and gemini_history[-1]["role"] == "user":
                    # flush via an assistant placeholder to keep alternating
                    gemini_history.append({"role": "model", "parts": ["Understood."]})
                gemini_history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                gemini_history.append({"role": "model", "parts": [msg.content]})

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        system_instruction = "\n\n".join(sys_parts) if sys_parts else None
        model = self._genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=system_instruction,
        )

        # Pop the last user message as the actual prompt
        history = gemini_history[:-1] if len(gemini_history) > 1 else []
        prompt = user_final or (gemini_history[-1]["parts"][0] if gemini_history else "")

        chat_session = model.start_chat(history=history)
        raw = chat_session.send_message(prompt)

        text = raw.text if hasattr(raw, "text") else str(raw)
        usage = getattr(raw, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        return LLMResponse(
            content=text,
            model=self.model_name,
            provider="gemini",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw=raw,
        )


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """
    Uses the openai SDK.
    Required env: OPENAI_API_KEY
    Optional env: OPENAI_MODEL (default: gpt-4o)
    """

    def __init__(self):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "openai is not installed. Run: pip install openai"
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )
        self._client = OpenAI(api_key=api_key)
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

    def chat(
        self,
        messages: List[LLMMessage | Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        msgs = self._coerce(messages)

        openai_msgs: List[Dict[str, str]] = []
        if system_prompt:
            openai_msgs.append({"role": "system", "content": system_prompt})

        for msg in msgs:
            openai_msgs.append({"role": msg.role, "content": msg.content})

        raw = self._client.chat.completions.create(
            model=self.model_name,
            messages=openai_msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = raw.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=raw.model,
            provider="openai",
            input_tokens=raw.usage.prompt_tokens if raw.usage else 0,
            output_tokens=raw.usage.completion_tokens if raw.usage else 0,
            finish_reason=choice.finish_reason or "stop",
            raw=raw,
        )


# ---------------------------------------------------------------------------
# Anthropic Claude
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """
    Uses the anthropic SDK.
    Required env: ANTHROPIC_API_KEY
    Optional env: ANTHROPIC_MODEL (default: claude-3-5-sonnet-20241022)
    """

    def __init__(self):
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "anthropic is not installed. Run: pip install anthropic"
            ) from exc

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model_name = os.getenv(
            "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"
        )

    def chat(
        self,
        messages: List[LLMMessage | Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        msgs = self._coerce(messages)

        sys_parts: List[str] = []
        if system_prompt:
            sys_parts.append(system_prompt)

        anthropic_msgs: List[Dict[str, str]] = []
        for msg in msgs:
            if msg.role == "system":
                sys_parts.append(msg.content)
            else:
                anthropic_msgs.append({"role": msg.role, "content": msg.content})

        raw = self._client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system="\n\n".join(sys_parts) if sys_parts else anthropic.NOT_GIVEN,
            messages=anthropic_msgs,
        )

        text = raw.content[0].text if raw.content else ""
        return LLMResponse(
            content=text,
            model=raw.model,
            provider="anthropic",
            input_tokens=raw.usage.input_tokens if raw.usage else 0,
            output_tokens=raw.usage.output_tokens if raw.usage else 0,
            finish_reason=raw.stop_reason or "stop",
            raw=raw,
        )


# ---------------------------------------------------------------------------
# Fallback stub (no API key required, heuristic-only mode)
# ---------------------------------------------------------------------------

class StubProvider(LLMProvider):
    """
    Returns a structured placeholder response when no LLM API key is available.
    Used automatically when LLM_PROVIDER is unset or keys are missing.
    Keeps all agents functional via their heuristic logic.
    """

    def chat(
        self,
        messages: List[LLMMessage | Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        msgs = self._coerce(messages)
        last_user = next(
            (m.content for m in reversed(msgs) if m.role == "user"),
            "No input provided",
        )
        content = (
            f"[StubProvider] LLM API key not configured. "
            f"Set LLM_PROVIDER and the corresponding API key in .env.\n"
            f"Received: {last_user[:200]}"
        )
        return LLMResponse(
            content=content, model="stub", provider="stub"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

_cached_provider: Optional[LLMProvider] = None


def get_llm_provider(provider: Optional[str] = None) -> LLMProvider:
    """
    Returns a singleton LLM provider instance.

    Args:
        provider: "gemini" | "openai" | "anthropic". Falls back to the
                  LLM_PROVIDER env var, then to StubProvider.

    Raises:
        ValueError: if an unrecognised provider name is supplied.
    """
    global _cached_provider

    if _cached_provider is not None and provider is None:
        return _cached_provider

    name = (provider or os.getenv("LLM_PROVIDER", "stub")).lower().strip()

    if name == "stub" or name == "":
        instance: LLMProvider = StubProvider()
    elif name in _PROVIDERS:
        try:
            instance = _PROVIDERS[name]()
        except (ImportError, EnvironmentError):
            # Graceful degradation — log and fall back to stub
            import warnings
            warnings.warn(
                f"Could not initialise '{name}' LLM provider. "
                "Falling back to StubProvider. "
                "Check your API key and installed packages.",
                stacklevel=2,
            )
            instance = StubProvider()
    else:
        raise ValueError(
            f"Unknown LLM provider '{name}'. "
            f"Valid options: {list(_PROVIDERS.keys())}"
        )

    if provider is None:
        _cached_provider = instance

    return instance


def reset_provider_cache() -> None:
    """Force the next get_llm_provider() call to re-initialise (useful in tests)."""
    global _cached_provider
    _cached_provider = None
