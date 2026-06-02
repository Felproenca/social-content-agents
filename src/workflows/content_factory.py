"""
ContentFactory: pipeline principal de criação de conteúdo.

Fluxo com NicheIntelligence:
  NicheIntelligenceAgent (descobre/carrega perfil do nicho)
  → ResearchAgent → TrendAgent + ProspectingAgent (paralelo)
  → CopyAgent (usa contexto de nicho)
  → DesignAgent + PerformanceAgent (paralelo)
  → [PublishingAgent]
"""

from dataclasses import dataclass, field
from typing import Any

from src.core.agent import AgentContext
from src.core.llm import build_provider
from src.core.models import NicheContext, NicheInput
from src.core.orchestrator import Orchestrator
from src.agents.research_agent import ResearchAgent
from src.agents.trend_agent import TrendAgent
from src.agents.copy_agent import CopyAgent
from src.agents.design_agent import DesignAgent
from src.agents.prospecting_agent import ProspectingAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.publishing_agent import PublishingAgent
from src.agents.niche_intelligence_agent import NicheIntelligenceAgent
from src.skills.niche_discovery import NicheDiscoverySkill


@dataclass
class ContentFactoryResult:
    topic: str
    platform: str
    niche_context: dict[str, Any] = field(default_factory=dict)
    copies: list[dict[str, Any]] = field(default_factory=list)
    visuals: list[dict[str, Any]] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)
    publish_status: dict[str, Any] = field(default_factory=dict)
    full_context: dict[str, Any] = field(default_factory=dict)


class ContentFactory:
    def __init__(self, orchestrator: Orchestrator | None = None):
        self.orchestrator = orchestrator or Orchestrator()
        self._provider = build_provider()
        self.discovery = NicheDiscoverySkill(llm=self._provider)
        self._register_agents()

    def _register_agents(self) -> None:
        for agent in [
            NicheIntelligenceAgent(discovery=self.discovery, provider=self._provider),
            ResearchAgent(provider=self._provider),
            TrendAgent(provider=self._provider),
            CopyAgent(provider=self._provider),
            DesignAgent(provider=self._provider),
            ProspectingAgent(provider=self._provider),
            PerformanceAgent(provider=self._provider),
            PublishingAgent(provider=self._provider),
        ]:
            self.orchestrator.register(agent)

    async def run(
        self,
        topic: str,
        platform: str = "linkedin",
        tone: str = "thought_leader",
        audience: str = "",
        objetivo: str = "awareness",
        tema: str | None = None,
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
                "objetivo": objetivo,
                "tema": tema,
                "niche_input": NicheInput(
                    nicho=topic,
                    objetivo=objetivo,
                    plataforma=platform,
                    tema=tema,
                ),
            },
        )

        # Step 0: NicheIntelligence — descobre/carrega perfil do nicho
        await self.orchestrator.run(["NicheIntelligenceAgent"], context)

        # Step 1: Research
        await self.orchestrator.run(["ResearchAgent"], context)

        # Step 2: Trend + Prospecting in parallel
        await self.orchestrator.run(["TrendAgent", "ProspectingAgent"], context, parallel=True)

        # Step 3: Copy (com contexto de nicho já disponível)
        await self.orchestrator.run(["CopyAgent"], context)

        # Step 4: Design + Performance in parallel
        await self.orchestrator.run(["DesignAgent", "PerformanceAgent"], context, parallel=True)

        # Step 5: Publish (only if requested)
        if auto_publish:
            await self.orchestrator.run(["PublishingAgent"], context)

        return ContentFactoryResult(
            topic=topic,
            platform=platform,
            niche_context=context.metadata.get("NicheIntelligenceAgent", {}),
            copies=context.metadata.get("CopyAgent", {}).get("copies", []),
            visuals=context.metadata.get("DesignAgent", {}).get("visuals", []),
            performance=context.metadata.get("PerformanceAgent", {}),
            publish_status=context.metadata.get("PublishingAgent", {}),
            full_context=context.metadata,
        )

    async def run_from_brief(self, brief: dict) -> ContentFactoryResult:
        """Ponto de entrada para briefs vindos do MarketingOS ou API."""
        return await self.run(
            topic=brief["nicho"],
            platform=brief.get("plataforma", "linkedin"),
            objetivo=brief.get("objetivo", "awareness"),
            tema=brief.get("tema"),
            tone=brief.get("tom", "thought_leader"),
            audience=brief.get("audiencia", ""),
        )
