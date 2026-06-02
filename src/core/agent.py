"""Base class for all agents in the framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import anthropic

from src.core.config import settings
from src.core.memory import Memory
from src.core.skill import Skill


@dataclass
class AgentContext:
    """Shared context passed between agents in a workflow."""

    topic: str = ""
    platform: str = ""
    tone: str = "professional"
    audience: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent: str
    success: bool
    output: dict[str, Any]
    error: str | None = None


class Agent(ABC):
    """
    Base agent. Wraps an LLM with a system prompt, a set of skills,
    and optional memory. Subclasses implement `run()`.
    """

    name: str
    role: str
    goal: str

    def __init__(self, memory: Memory | None = None):
        self.memory = memory or Memory()
        self.skills: list[Skill] = []
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    def register_skill(self, skill: Skill) -> None:
        self.skills.append(skill)

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent's task and return a result."""
        ...

    async def _chat(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        use_tools: bool = True,
        max_tokens: int = 4096,
    ) -> anthropic.types.Message:
        kwargs: dict[str, Any] = {
            "model": settings.llm_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if use_tools and self.skills:
            kwargs["tools"] = [s.to_tool_definition() for s in self.skills]

        return await self._client.messages.create(**kwargs)

    def _system_prompt(self) -> str:
        return (
            f"Você é {self.name}.\n"
            f"Papel: {self.role}\n"
            f"Objetivo: {self.goal}\n\n"
            "Responda sempre em português do Brasil, de forma clara e estruturada."
        )
