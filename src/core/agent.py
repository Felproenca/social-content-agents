"""Base class for all agents in the framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.core.memory import Memory
from src.core.skill import Skill
from src.core.llm import LLMProvider, LLMResponse, build_provider


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
    Base agent. Wraps an LLM provider with a system prompt, a set of skills,
    and optional memory. Subclasses implement `run()`.

    Por padrão usa o Claude Code CLI (VS Code) — sem precisar de API key.
    Para usar a API Anthropic diretamente, defina LLM_PROVIDER=anthropic
    e ANTHROPIC_API_KEY no .env.
    """

    name: str
    role: str
    goal: str

    def __init__(self, memory: Memory | None = None, provider: LLMProvider | None = None):
        self.memory = memory or Memory()
        self.skills: list[Skill] = []
        self._provider = provider or build_provider()

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
        use_tools: bool = False,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return await self._provider.chat(
            messages=messages,
            system=system,
            max_tokens=max_tokens,
        )

    def _system_prompt(self) -> str:
        return (
            f"Você é {self.name}.\n"
            f"Papel: {self.role}\n"
            f"Objetivo: {self.goal}\n\n"
            "Responda sempre em português do Brasil, de forma clara e estruturada."
        )
