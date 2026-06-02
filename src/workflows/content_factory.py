"""
ContentFactory: pipeline principal de criação de conteúdo.

Fluxo com NicheIntelligence + VisualSpec + PromptEngineer (híbrido):
  NicheIntelligenceAgent
  → ResearchAgent
  → TrendAgent + ProspectingAgent (paralelo)
  → CopyAgent
  → VisualSpecAgent + PerformanceAgent (paralelo)
  → PromptEngineerAgent (decide HTML-only vs imagem externa)
  → se ready_to_render: HTMLRenderer → PuppeteerExporter
  → se aguardando imagem: pausa, notifica operador, salva status
"""

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.agent import AgentContext
from src.core.llm import build_provider
from src.core.models import (
    ClientContext, ClientPalette, ClientTypography,
    NicheInput, PipelineStatus, SlideProcessingMode,
    VisualSpec, VisualStyle,
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
from src.agents.prompt_engineer_agent import PromptEngineerAgent
from src.skills.niche_discovery import NicheDiscoverySkill
from src.skills.html_renderer import HTMLRenderer
from src.skills.operator_notifier import OperatorNotifier


@dataclass
class ContentFactoryResult:
    topic: str
    platform: str
    status: str = "completo"          # completo | aguardando_imagens
    content_id: str = ""
    niche_context: dict[str, Any] = field(default_factory=dict)
    copies: list[dict[str, Any]] = field(default_factory=list)
    visual_spec: VisualSpec | None = None
    pipeline_status: PipelineStatus | None = None
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
        self.prompt_engineer = PromptEngineerAgent(provider=self._provider)
        self.html_renderer = HTMLRenderer()
        self._notifier = OperatorNotifier()
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

        visual_spec: VisualSpec | None = None
        html_paths: list[Path] = []
        png_paths: list[Path] = []
        pipeline_status: PipelineStatus | None = None
        content_id = ""
        result_status = "completo"

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
                content_id = self._generate_content_id(topic, client_context.slug)
                pipeline_status = await self.prompt_engineer.analyze(visual_spec, content_id)

                if not pipeline_status.ready_to_render:
                    notification = self._notifier.format_notification(pipeline_status)
                    print(notification)
                    output_dir = Path(f"tmp/{client_context.slug}/slides")
                    html_paths = await self.html_renderer.render(visual_spec, output_dir)
                    await self.save_pipeline_status(pipeline_status, client_context.slug)
                    result_status = "aguardando_imagens"
                else:
                    output_dir = Path(f"tmp/{client_context.slug}/slides")
                    html_paths = await self.html_renderer.render(visual_spec, output_dir)

        return ContentFactoryResult(
            topic=topic,
            platform=platform,
            status=result_status,
            content_id=content_id,
            niche_context=context.metadata.get("NicheIntelligenceAgent", {}),
            copies=copies,
            visual_spec=visual_spec,
            pipeline_status=pipeline_status,
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

        if result.status == "aguardando_imagens":
            return result

        # Export PNGs if pyppeteer available and HTML was generated
        if result.html_paths and client_context:
            result.png_paths = await self._try_export_pngs(
                result.html_paths, client_context.slug, brief.get("format", "1:1")
            )

        return result

    async def resume_after_images(self, content_id: str, client_slug: str) -> ContentFactoryResult:
        """
        Retoma o pipeline após todas as imagens terem sido uploadadas.
        Chamado pelo CLI upload-image quando todos os slides ficam IMAGE_READY.
        """
        pipeline_status = await self.load_pipeline_status(content_id, client_slug)
        if pipeline_status is None:
            raise FileNotFoundError(f"Status não encontrado para content_id={content_id}")

        if not pipeline_status.ready_to_render:
            pending = [p.slide_number for p in pipeline_status.image_prompts
                       if p.status != SlideProcessingMode.IMAGE_READY]
            raise RuntimeError(f"Slides ainda aguardando imagem: {pending}")

        html_dir = Path(f"tmp/{client_slug}/slides")
        png_paths = await self._try_export_pngs(
            list(html_dir.glob("slide-*.html")), client_slug, "1:1"
        )

        return ContentFactoryResult(
            topic=content_id,
            platform="",
            status="completo",
            content_id=content_id,
            pipeline_status=pipeline_status,
            html_paths=list(html_dir.glob("slide-*.html")),
            png_paths=png_paths,
        )

    # ── persistence ───────────────────────────────────────────────────────────

    async def save_pipeline_status(self, status: PipelineStatus, client_slug: str) -> Path:
        status_dir = Path(f"tmp/{client_slug}/status")
        status_dir.mkdir(parents=True, exist_ok=True)
        path = status_dir / f"{status.content_id}.json"
        path.write_text(
            json.dumps(dataclasses.asdict(status), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    async def load_pipeline_status(
        self, content_id: str, client_slug: str
    ) -> PipelineStatus | None:
        path = Path(f"tmp/{client_slug}/status/{content_id}.json")
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return self._dict_to_pipeline_status(data)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_content_id(topic: str, client_slug: str = "") -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = topic.lower()[:20].replace(" ", "-").replace("/", "-")
        prefix = f"{client_slug}-" if client_slug else ""
        return f"{prefix}{slug}-{ts}"

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

    @staticmethod
    def _dict_to_pipeline_status(data: dict) -> PipelineStatus:
        from src.core.models import ImagePrompt
        prompts = [
            ImagePrompt(
                slide_number=p["slide_number"],
                prompt_en=p["prompt_en"],
                prompt_pt=p["prompt_pt"],
                negative=p["negative"],
                style_notes=p["style_notes"],
                aspect_ratio=p["aspect_ratio"],
                service_hints=p["service_hints"],
                status=SlideProcessingMode(p["status"]),
                image_path=p.get("image_path"),
            )
            for p in data.get("image_prompts", [])
        ]
        return PipelineStatus(
            client_slug=data["client_slug"],
            content_id=data["content_id"],
            total_slides=data["total_slides"],
            html_only=data["html_only"],
            needs_image=data["needs_image"],
            image_prompts=prompts,
            ready_to_render=data["ready_to_render"],
            rendered_pngs=data.get("rendered_pngs", []),
        )
