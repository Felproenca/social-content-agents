"""Orchestrator: routes tasks between agents and collects results."""

import asyncio
import logging
from typing import Any

from src.core.agent import Agent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Manages a registry of agents and runs them sequentially or in parallel.
    Results are accumulated and passed downstream as context metadata.
    """

    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent
        logger.debug("Registered agent: %s", agent.name)

    async def run_sequential(
        self, agent_names: list[str], context: AgentContext
    ) -> list[AgentResult]:
        results: list[AgentResult] = []
        for name in agent_names:
            agent = self._agents[name]
            result = await agent.run(context)
            results.append(result)
            # Merge output into context metadata for downstream agents
            context.metadata[name] = result.output
            if not result.success:
                logger.warning("Agent %s failed: %s", name, result.error)
        return results

    async def run_parallel(
        self, agent_names: list[str], context: AgentContext
    ) -> list[AgentResult]:
        tasks = [self._agents[name].run(context) for name in agent_names]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        for name, result in zip(agent_names, results):
            context.metadata[name] = result.output
        return list(results)

    async def run(
        self,
        agent_names: list[str],
        context: AgentContext,
        parallel: bool = False,
    ) -> list[AgentResult]:
        if parallel:
            return await self.run_parallel(agent_names, context)
        return await self.run_sequential(agent_names, context)

    def get_agent(self, name: str) -> Agent:
        return self._agents[name]

    @property
    def agents(self) -> dict[str, Agent]:
        return dict(self._agents)
