"""LLM providers plugáveis. Padrão: Claude Code CLI (sem API key)."""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any


class LLMResponse:
    def __init__(self, text: str):
        self.text = text

    @property
    def content(self) -> list:
        return [self]


class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...

    async def generate(
        self,
        user: str,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Convenience wrapper: single user message → plain text response."""
        response = await self.chat(
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        return response.text


class ClaudeCodeProvider(LLMProvider):
    """
    Usa o CLI `claude` já autenticado no VS Code.
    Não exige ANTHROPIC_API_KEY — aproveita a sessão ativa do Claude Code.
    """

    def __init__(self, model: str = ""):
        self._model = model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # Build a single prompt from the messages list
        prompt_parts = []
        if system:
            prompt_parts.append(f"<system>\n{system}\n</system>\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(content)
            elif role == "assistant":
                prompt_parts.append(f"[Assistant]: {content}")

        full_prompt = "\n\n".join(prompt_parts)

        cmd = ["claude", "-p", full_prompt, "--output-format", "text"]
        if self._model:
            cmd += ["--model", self._model]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error = stderr.decode().strip()
            raise RuntimeError(f"claude CLI error (code {proc.returncode}): {error}")

        return LLMResponse(stdout.decode().strip())


class AnthropicProvider(LLMProvider):
    """Chama a API Anthropic diretamente com ANTHROPIC_API_KEY."""

    def __init__(self, api_key: str, model: str):
        import anthropic as _anthropic
        self._client = _anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)
        return LLMResponse(response.content[0].text)


def build_provider() -> LLMProvider:
    from src.core.config import settings

    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )

    # Padrão: Claude Code CLI (VS Code / terminal autenticado)
    return ClaudeCodeProvider(model=settings.llm_model)
