"""
ContentFactory: pipeline principal de criação de conteúdo.

Fluxo com NicheIntelligence + VisualSpec:
  NicheIntelligenceAgent
  → ResearchAgent
  → TrendAgent + ProspectingAgent (paralelo)
  → CopyAgent
  → VisualSpecAgent + PerformanceAgent (paralelo)
  → HTMLRenderer → PuppeteerExporter
  → [PublishingAgent]
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.agent import AgentContext
from src.core.llm import build_provider
from src.core.models import (
    ClientContext, ClientPalette, ClientTypography,
    NicheInput, VisualSpec, VisualStyle,
)
from src.core.orchestrator import Orchestrator
from src.agents.research_agent import ResearchAgent
from src.agents.trend_agent import TrendAgent
from src.agents.copy_agent import CopyAgent
from src.agents.design_agent import DesignAgent
from src.agents.prospecting_agent import ProspectingAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.publishing_agent import PublishingAgent
from src.agents.niche_intelligence_agent import NicheIntelligenceAgent
from src.agents.visual_spec_agent import VisualSpecAgent
from src.skills.niche_discovery import NicheDiscoverySkill
from src.skills.html_renderer import HTMLRenderer


@dataclass
class ContentFactoryResult:
    topic: str
    platform: str
    niche_context: dict[str, Any] = field(default_factory=dict)
    copies: list[dict[str, Any]] = field(default_factory=list)
    visual_spec: VisualSpec | None = None
    html_paths: list[Path] = field(default_factory=list)
    png_paths: list[Path] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)
    publish_status: dict[str, Any] = field(default_factory=dict)
    full_context: dict[str, Any] = field(default_factory=dict)


class ContentFactory:
    def __init__(self, orchestrator: Orchestrator | None = None):
        self.orchestrator = orchestrator or Orchestrator()
        self._provider = build_provider()
        self.discovery = NicheDiscoverySkill(llm=self._provider)
        self.visual_spec_agent = VisualSpecAgent(provider=self._provider)
        self.html_renderer = HTMLRenderer()
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
        client_context: ClientContext | None = None,
        enable_visual: bool = False,
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
                "client_context": client_context,
            },
        )

        await self.orchestrator.run(["NicheIntelligenceAgent"], context)
        await self.orchestrator.run(["ResearchAgent"], context)
        await self.orchestrator.run(["TrendAgent", "ProspectingAgent"], context, parallel=True)
        await self.orchestrator.run(["CopyAgent"], context)
        await self.orchestrator.run(["PerformanceAgent"], context)

        if auto_publish:
            await self.orchestrator.run(["PublishingAgent"], context)

        copies = context.metadata.get("CopyAgent", {}).get("copies", [])

        # Visual pipeline (opt-in)
        visual_spec: VisualSpec | None = None
        html_paths: list[Path] = []
        png_paths: list[Path] = []

        if enable_visual and client_context is not None:
            niche_data = context.metadata.get("NicheIntelligenceAgent", {})
            niche_ctx = niche_data.get("_niche_context")
            if niche_ctx and copies:
                visual_spec = await self.visual_spec_agent.generate(
                    client=client_context,
                    niche_context=niche_ctx,
                    copies=self._copies_to_slides(copies),
                    platform=platform,
                )
                output_dir = Path(f"tmp/{client_context.slug}/slides")
                html_paths = await self.html_renderer.render(visual_spec, output_dir)

        return ContentFactoryResult(
            topic=topic,
            platform=platform,
            niche_context=context.metadata.get("NicheIntelligenceAgent", {}),
            copies=copies,
            visual_spec=visual_spec,
            html_paths=html_paths,
            png_paths=png_paths,
            performance=context.metadata.get("PerformanceAgent", {}),
            publish_status=context.metadata.get("PublishingAgent", {}),
            full_context=context.metadata,
        )

    async def run_from_brief(self, brief: dict) -> ContentFactoryResult:
        """
        Ponto de entrada para briefs vindos do MarketingOS ou API.
        Quando 'contexto_cliente' estiver presente, gera o pipeline visual completo.
        """
        client_context = self._build_client_context(brief)
        enable_visual = client_context is not None

        result = await self.run(
            topic=brief["nicho"],
            platform=brief.get("plataforma", "linkedin"),
            objetivo=brief.get("objetivo", "awareness"),
            tema=brief.get("tema"),
            tone=brief.get("tom", "thought_leader"),
            audience=brief.get("audiencia", ""),
            client_context=client_context,
            enable_visual=enable_visual,
        )

        # Export PNGs if pyppeteer available and HTML was generated
        if result.html_paths and client_context:
            result.png_paths = await self._try_export_pngs(
                result.html_paths, client_context.slug, brief.get("format", "1:1")
            )

        return result

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_client_context(self, brief: dict) -> ClientContext | None:
        ctx = brief.get("contexto_cliente")
        if not ctx:
            return None
        try:
            raw_palette = ctx.get("palette", {})
            raw_typo = ctx.get("typography", {})
            return ClientContext(
                slug=brief.get("client_slug", "cliente"),
                name=ctx.get("nome", "Cliente"),
                palette=ClientPalette(
                    primary=raw_palette.get("primary", "#000000"),
                    secondary=raw_palette.get("secondary", "#333333"),
                    accent=raw_palette.get("accent", "#0066ff"),
                    background=raw_palette.get("background", "#ffffff"),
                    text=raw_palette.get("text", "#1a1a1a"),
                    text_light=raw_palette.get("text_light", "#888888"),
                ),
                typography=ClientTypography(
                    heading=raw_typo.get("heading", "Playfair Display"),
                    body=raw_typo.get("body", "Inter"),
                ),
                style=VisualStyle.CLEAN,
                nicho=brief.get("nicho", ""),
            )
        except (KeyError, TypeError):
            return None

    def _copies_to_slides(self, copies: list[dict]) -> list[dict]:
        """Normaliza copies do CopyAgent para o formato de slides do VisualSpecAgent."""
        slides = []
        for copy in copies:
            slides.append({
                "headline": copy.get("hook", copy.get("headline", "")),
                "body":     copy.get("body", ""),
                "cta":      copy.get("cta", ""),
                "has_data": self._has_data(copy.get("body", "")),
            })
        return slides

    @staticmethod
    def _has_data(text: str) -> bool:
        import re
        return bool(re.search(r"\d+[%xk+]", text or ""))

    async def _try_export_pngs(
        self, html_paths: list[Path], client_slug: str, format: str
    ) -> list[Path]:
        try:
            from src.skills.puppeteer_exporter import PuppeteerExporter
            from src.skills.html_renderer import FORMATS
            w, h = FORMATS.get(format, (1080, 1080))
            exporter = PuppeteerExporter(width=w, height=h)
            output_dir = Path(f"tmp/{client_slug}/slides/png")
            return await exporter.export(html_paths, output_dir)
        except (ImportError, Exception):
            return []
