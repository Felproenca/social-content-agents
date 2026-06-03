"""
Tests for PromptEngineerAgent hybrid flow.

Three core scenarios:
1. All tipographic slides → zero external image prompts
2. Editorial gancho (FOTO_TEXTO + image-overlay) → exactly 1 prompt
3. Mixed carousel: 1 gancho foto + 3 conteudo + 1 cta → exactly 1 prompt
"""

import pytest

from src.agents.prompt_engineer_agent import PromptEngineerAgent
from src.core.models import (
    ClientContext, ClientPalette, ClientTypography,
    EditorialPosition, NicheContext, NicheLanguage,
    PipelineStatus, SlideProcessingMode, SlideRole,
    SlideSpec, TopicMaturity, VisualSpec, VisualStyle, VisualType,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

def _client() -> ClientContext:
    return ClientContext(
        slug="test-client",
        name="Test Client",
        palette=ClientPalette(
            primary="#000000", secondary="#333333", accent="#0066ff",
            background="#ffffff", text="#1a1a1a", text_light="#888888",
        ),
        typography=ClientTypography(heading="Inter", body="Inter"),
        style=VisualStyle.CLEAN,
        nicho="marketing digital",
    )


def _niche_ctx() -> NicheContext:
    return NicheContext(
        angulo="Ângulo teste",
        linguagem=NicheLanguage(usa=[], evita=[], tom="direto", nivel_tecnico="praticante"),
        posicao=EditorialPosition.EDUCACAO,
        o_que_evitar=[],
        referencias=[],
        tendencia_status=TopicMaturity.MAINSTREAM,
        hook_direction="provocar",
        insights_exclusivos=[],
    )


def _make_slide(
    number: int,
    role: SlideRole,
    visual_type: VisualType,
    bg: str = "solid",
    total: int = 5,
) -> SlideSpec:
    return SlideSpec(
        role=role,
        slide_number=number,
        total_slides=total,
        headline=f"Headline {number}",
        body=f"Body {number}",
        visual_type=visual_type,
        layout="center",
        focal_point="centro",
        emphasis=[],
        cta=None,
        background_treatment=bg,
    )


def _make_spec(slides: list[SlideSpec]) -> VisualSpec:
    return VisualSpec(
        client=_client(),
        niche_context=_niche_ctx(),
        style=VisualStyle.CLEAN,
        visual_type=VisualType.TIPOGRAFICO,
        mood="profissional",
        format="1:1",
        slides=slides,
        global_css="",
    )


# ── tests ─────────────────────────────────────────────────────────────────────

class TestNeedsExternalImage:
    """Unit tests for the static 3-condition gate."""

    def test_tipografico_never_needs_image(self):
        slide = _make_slide(1, SlideRole.GANCHO, VisualType.TIPOGRAFICO, "image-overlay")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_dados_never_needs_image(self):
        slide = _make_slide(1, SlideRole.GANCHO, VisualType.DADOS, "image-overlay")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_screenshot_never_needs_image(self):
        slide = _make_slide(1, SlideRole.GANCHO, VisualType.SCREENSHOT, "image-overlay")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_cta_never_needs_image(self):
        slide = _make_slide(5, SlideRole.CTA, VisualType.FOTO_TEXTO, "image-overlay")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_conteudo_never_needs_image(self):
        slide = _make_slide(2, SlideRole.CONTEUDO, VisualType.FOTO_TEXTO, "image-overlay")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_gancho_foto_texto_solid_no_image(self):
        slide = _make_slide(1, SlideRole.GANCHO, VisualType.FOTO_TEXTO, "solid")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_gancho_foto_texto_gradient_no_image(self):
        slide = _make_slide(1, SlideRole.GANCHO, VisualType.FOTO_TEXTO, "gradient")
        assert PromptEngineerAgent._needs_external_image(slide) is False

    def test_gancho_foto_texto_image_overlay_needs_image(self):
        slide = _make_slide(1, SlideRole.GANCHO, VisualType.FOTO_TEXTO, "image-overlay")
        assert PromptEngineerAgent._needs_external_image(slide) is True


class TestAnalyzeAllHtmlOnly:
    """All tipographic slides → no prompts, pipeline immediately ready."""

    @pytest.mark.asyncio
    async def test_tipographic_carousel_ready_to_render(self, monkeypatch):
        slides = [
            _make_slide(1, SlideRole.GANCHO, VisualType.TIPOGRAFICO),
            _make_slide(2, SlideRole.CONTEUDO, VisualType.TIPOGRAFICO),
            _make_slide(3, SlideRole.CONTEUDO, VisualType.TIPOGRAFICO),
            _make_slide(4, SlideRole.PROVA, VisualType.DADOS),
            _make_slide(5, SlideRole.CTA, VisualType.TIPOGRAFICO),
        ]
        spec = _make_spec(slides)

        agent = PromptEngineerAgent()
        # _generate_prompt should never be called
        called = []
        monkeypatch.setattr(agent, "_generate_prompt", lambda *a, **k: called.append(1))

        status = await agent.analyze(spec, "test-001")

        assert status.ready_to_render is True
        assert status.needs_image == []
        assert status.html_only == [1, 2, 3, 4, 5]
        assert status.image_prompts == []
        assert called == []


class TestAnalyzeOneGanchoFoto:
    """Editorial gancho with FOTO_TEXTO + image-overlay → exactly 1 prompt generated."""

    @pytest.mark.asyncio
    async def test_one_prompt_generated(self, monkeypatch):
        from src.core.models import ImagePrompt

        slides = [
            _make_slide(1, SlideRole.GANCHO, VisualType.FOTO_TEXTO, "image-overlay"),
            _make_slide(2, SlideRole.CONTEUDO, VisualType.TIPOGRAFICO),
            _make_slide(3, SlideRole.CONTEUDO, VisualType.TIPOGRAFICO),
            _make_slide(4, SlideRole.PROVA, VisualType.DADOS),
            _make_slide(5, SlideRole.CTA, VisualType.TIPOGRAFICO),
        ]
        spec = _make_spec(slides)

        fake_prompt = ImagePrompt(
            slide_number=1,
            prompt_en="wide angle shot",
            prompt_pt="foto grande angular",
            negative="stock photo",
            style_notes="dark tones",
            aspect_ratio="1:1",
            service_hints={},
            status=SlideProcessingMode.NEEDS_IMAGE,
        )

        agent = PromptEngineerAgent()
        monkeypatch.setattr(
            agent, "_generate_prompt",
            lambda slide, spec_arg: _coro(fake_prompt),
        )

        status = await agent.analyze(spec, "test-002")

        assert status.ready_to_render is False
        assert status.needs_image == [1]
        assert status.html_only == [2, 3, 4, 5]
        assert len(status.image_prompts) == 1
        assert status.image_prompts[0].slide_number == 1
        assert status.image_prompts[0].status == SlideProcessingMode.NEEDS_IMAGE


class TestAnalyzeMixedCarousel:
    """Multiple slides, only the qualifying gancho triggers a prompt."""

    @pytest.mark.asyncio
    async def test_only_qualifying_gancho_gets_prompt(self, monkeypatch):
        from src.core.models import ImagePrompt

        slides = [
            # qualifies
            _make_slide(1, SlideRole.GANCHO, VisualType.FOTO_TEXTO, "image-overlay"),
            # foto_texto but not gancho
            _make_slide(2, SlideRole.CONTEUDO, VisualType.FOTO_TEXTO, "image-overlay"),
            # hibrido gancho but not image-overlay
            _make_slide(3, SlideRole.GANCHO, VisualType.HIBRIDO, "gradient"),
            _make_slide(4, SlideRole.PROVA, VisualType.DADOS),
            _make_slide(5, SlideRole.CTA, VisualType.FOTO_TEXTO, "image-overlay"),
        ]
        spec = _make_spec(slides)

        call_count = 0

        async def fake_generate(slide, spec_arg):
            nonlocal call_count
            call_count += 1
            return ImagePrompt(
                slide_number=slide.slide_number,
                prompt_en="test", prompt_pt="teste",
                negative="", style_notes="",
                aspect_ratio="1:1", service_hints={},
                status=SlideProcessingMode.NEEDS_IMAGE,
            )

        agent = PromptEngineerAgent()
        monkeypatch.setattr(agent, "_generate_prompt", fake_generate)

        status = await agent.analyze(spec, "test-003")

        assert call_count == 1
        assert status.needs_image == [1]
        assert set(status.html_only) == {2, 3, 4, 5}
        assert status.ready_to_render is False


# ── helper ────────────────────────────────────────────────────────────────────

async def _coro(value):
    return value
