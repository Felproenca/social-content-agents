"""
ContentFactory: pipeline principal de criação de conteúdo.

Fluxo:
  ResearchAgent → TrendAgent (paralelo com ProspectingAgent)
  → CopyAgent → DesignAgent → PerformanceAgent → [PublishingAgent]
"""

from dataclasses import dataclass, field
from typing import Any

from src.core.agent import AgentContext
from src.core.orchestrator import Orchestrator
from src.agents.research_agent import ResearchAgent
from src.agents.trend_agent import TrendAgent
from src.agents.copy_agent import CopyAgent
from src.agents.design_agent import DesignAgent
from src.agents.prospecting_agent import ProspectingAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.publishing_agent import PublishingAgent


@dataclass
class ContentFactoryResult:
    topic: str
    platform: str
    copies: list[dict[str, Any]] = field(default_factory=list)
    visuals: list[dict[str, Any]] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)
    publish_status: dict[str, Any] = field(default_factory=dict)
    full_context: dict[str, Any] = field(default_factory=dict)


class ContentFactory:
    def __init__(self, orchestrator: Orchestrator | None = None):
        self.orchestrator = orchestrator or Orchestrator()
        self._register_agents()

    def _register_agents(self) -> None:
        for agent in [
            ResearchAgent(),
            TrendAgent(),
            CopyAgent(),
            DesignAgent(),
            ProspectingAgent(),
            PerformanceAgent(),
            PublishingAgent(),
        ]:
            self.orchestrator.register(agent)

    async def run(
        self,
        topic: str,
        platform: str = "linkedin",
        tone: str = "thought_leader",
        audience: str = "",
        variations: int = 3,
        auto_publish: bool = False,
        historical_metrics: list | None = None,
    ) -> ContentFactoryResult:
        context = AgentContext(
            topic=topic,
            platform=platform,
            tone=tone,
            audience=audience,
            metadata={
                "copy_variations": variations,
                "metrics": historical_metrics or [],
            },
        )

        # Step 1: Research
        await self.orchestrator.run(["ResearchAgent"], context)

        # Step 2: Trend + Prospecting in parallel
        await self.orchestrator.run(["TrendAgent", "ProspectingAgent"], context, parallel=True)

        # Step 3: Copy
        await self.orchestrator.run(["CopyAgent"], context)

        # Step 4: Design + Performance in parallel
        await self.orchestrator.run(["DesignAgent", "PerformanceAgent"], context, parallel=True)

        # Step 5: Publish (only if requested)
        if auto_publish:
            await self.orchestrator.run(["PublishingAgent"], context)

        copies = context.metadata.get("CopyAgent", {}).get("copies", [])
        visuals = context.metadata.get("DesignAgent", {}).get("visuals", [])
        performance = context.metadata.get("PerformanceAgent", {})
        publish_status = context.metadata.get("PublishingAgent", {})

        return ContentFactoryResult(
            topic=topic,
            platform=platform,
            copies=copies,
            visuals=visuals,
            performance=performance,
            publish_status=publish_status,
            full_context=context.metadata,
        )
