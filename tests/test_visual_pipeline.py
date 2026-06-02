"""
Testa o pipeline visual com 3 combinações:
  1. Cliente dark + nicho IA + carrossel técnico
  2. Cliente clean + nicho saúde + carrossel editorial
  3. Cliente bold + nicho jurídico + post único
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.core.llm import LLMProvider, LLMResponse
from src.core.models import (
    ClientContext, ClientPalette, ClientTypography,
    EditorialPosition, NicheContext, NicheLanguage,
    SlideRole, TopicMaturity, VisualSpec, VisualStyle, VisualType,
)
from src.agents.visual_spec_agent import VisualSpecAgent, POSITION_TO_STYLE
from src.skills.html_renderer import HTMLRenderer


# ── Fixtures ──────────────────────────────────────────────────────────────────

class FakeLLMProvider(LLMProvider):
    def __init__(self, response: str = "urgente e direto"):
        self._response = response

    async def chat(self, messages, system=None, max_tokens=4096):
        return LLMResponse(self._response)


def _make_niche_context(posicao: EditorialPosition = EditorialPosition.PROVOCACAO) -> NicheContext:
    return NicheContext(
        angulo="Verdade incômoda do setor",
        linguagem=NicheLanguage(
            usa=["ROI real", "CAC", "LTV"],
            evita=["soluções inovadoras", "parceria estratégica"],
            tom="direto e técnico",
            nivel_tecnico="especialista",
        ),
        posicao=posicao,
        o_que_evitar=["Frase batida 1"],
        referencias=["Referência A"],
        tendencia_status=TopicMaturity.ASCENDENDO,
        hook_direction="Começa com a afirmação que desafia",
        insights_exclusivos=["Insight 1", "Insight 2"],
    )


def _make_client(style: VisualStyle, nicho: str = "tecnologia") -> ClientContext:
    return ClientContext(
        slug="empresa-teste",
        name="Empresa Teste",
        palette=ClientPalette(
            primary="#0c2137",
            secondary="#162d45",
            accent="#c9a55c",
            background="#f0ebe2",
            text="#1a1208",
            text_light="#9a8d7a",
        ),
        typography=ClientTypography(heading="Playfair Display", body="Syne"),
        style=style,
        nicho=nicho,
    )


def _make_copies(n: int = 3) -> list[dict]:
    copies = []
    for i in range(n):
        copies.append({
            "headline": f"Headline do slide {i + 1}",
            "hook":     f"Gancho impactante {i + 1}",
            "body":     f"Corpo do conteúdo do slide {i + 1}. Detalha o ponto principal.",
            "cta":      "Fale com a gente" if i == n - 1 else None,
        })
    return copies


# ── VisualSpecAgent — determine_style ─────────────────────────────────────────

def test_derive_style_from_client_explicit():
    """Cliente com style != CLEAN → usa o estilo do cliente."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.DARK)
    niche_ctx = _make_niche_context()
    assert agent._determine_style(client, niche_ctx) == VisualStyle.DARK


def test_derive_style_from_nicho_hint():
    """Cliente CLEAN + nicho com hint → usa hint do nicho."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.CLEAN, nicho="inteligencia artificial")
    niche_ctx = _make_niche_context()
    assert agent._determine_style(client, niche_ctx) == VisualStyle.TECHNICAL


def test_derive_style_from_editorial_position():
    """Cliente CLEAN + nicho sem hint → deriva da posição editorial."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.CLEAN, nicho="nicho-desconhecido-xyz")
    niche_ctx = _make_niche_context(EditorialPosition.PROVOCACAO)
    assert agent._determine_style(client, niche_ctx) == VisualStyle.BOLD


# ── VisualSpecAgent — slide roles ─────────────────────────────────────────────

def test_first_slide_is_gancho():
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    role = agent._determine_role(0, 5, {})
    assert role == SlideRole.GANCHO


def test_last_slide_is_cta():
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    role = agent._determine_role(4, 5, {})
    assert role == SlideRole.CTA


def test_slide_with_data_is_prova():
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    role = agent._determine_role(2, 5, {"has_data": True})
    assert role == SlideRole.PROVA


# ── VisualSpecAgent — generate ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_dark_ia_carrossel():
    """Cenário 1: cliente dark + nicho IA + carrossel técnico."""
    agent = VisualSpecAgent(provider=FakeLLMProvider("técnico e confiável"))
    client = _make_client(VisualStyle.DARK, nicho="inteligencia artificial")
    niche_ctx = _make_niche_context(EditorialPosition.DEMONSTRACAO)
    copies = _make_copies(5)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)

    assert isinstance(spec, VisualSpec)
    assert spec.style == VisualStyle.DARK  # cliente definiu explicitamente
    assert len(spec.slides) == 5
    assert spec.slides[0].role == SlideRole.GANCHO
    assert spec.slides[-1].role == SlideRole.CTA
    assert "técnico" in spec.mood.lower() or len(spec.mood) > 0
    assert "--primary" in spec.global_css
    assert "#0a0a0a" in spec.global_css  # dark style override


@pytest.mark.asyncio
async def test_generate_clean_saude_editorial():
    """Cenário 2: cliente clean + nicho saúde + estilo editorial derivado."""
    agent = VisualSpecAgent(provider=FakeLLMProvider("premium e calmo"))
    client = _make_client(VisualStyle.CLEAN, nicho="saude estetica")
    niche_ctx = _make_niche_context(EditorialPosition.EDUCACAO)
    copies = _make_copies(4)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)

    assert isinstance(spec, VisualSpec)
    assert len(spec.slides) == 4
    assert "#ffffff" in spec.global_css  # clean style override


@pytest.mark.asyncio
async def test_generate_bold_juridico_post_unico():
    """Cenário 3: cliente bold + nicho jurídico + post único."""
    agent = VisualSpecAgent(provider=FakeLLMProvider("ousado e direto"))
    client = _make_client(VisualStyle.BOLD, nicho="juridico")
    niche_ctx = _make_niche_context(EditorialPosition.PROVOCACAO)
    copies = _make_copies(1)  # post único

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)

    assert isinstance(spec, VisualSpec)
    assert spec.style == VisualStyle.BOLD
    assert len(spec.slides) == 1
    # Post único: slide 0 é GANCHO, mas como é também o último, torna-se CTA
    assert spec.slides[0].role in (SlideRole.GANCHO, SlideRole.CTA)
    assert "text-transform: uppercase" in spec.global_css or "BOLD" in spec.style.value.upper()


# ── HTMLRenderer ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_html_renderer_produces_files():
    """HTMLRenderer deve criar um HTML por slide."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.CLEAN)
    niche_ctx = _make_niche_context()
    copies = _make_copies(3)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)

    renderer = HTMLRenderer()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        html_paths = await renderer.render(spec, out)

        assert len(html_paths) == 3
        for path in html_paths:
            assert path.exists()
            content = path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "--primary" in content
            assert "empresa-teste" in content  # client slug no mark


@pytest.mark.asyncio
async def test_html_gancho_has_h1():
    """Slide GANCHO deve usar tag h1."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.BOLD)
    niche_ctx = _make_niche_context(EditorialPosition.PROVOCACAO)
    copies = _make_copies(3)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)
    renderer = HTMLRenderer()

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        html_paths = await renderer.render(spec, out)
        gancho_html = html_paths[0].read_text()
        assert '<h1 class="headline">' in gancho_html


@pytest.mark.asyncio
async def test_html_cta_slide_has_cta_action():
    """Slide CTA deve ter a div .cta-action."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.CLEAN)
    niche_ctx = _make_niche_context()
    copies = _make_copies(3)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)
    renderer = HTMLRenderer()

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        html_paths = await renderer.render(spec, out)
        cta_html = html_paths[-1].read_text()
        assert 'cta-action' in cta_html


@pytest.mark.asyncio
async def test_html_technical_style_has_grid():
    """Estilo TECHNICAL deve incluir CSS de grid overlay."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.TECHNICAL)
    niche_ctx = _make_niche_context()
    copies = _make_copies(2)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)
    renderer = HTMLRenderer()

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        html_paths = await renderer.render(spec, out)
        html = html_paths[0].read_text()
        assert "background-size: 40px 40px" in html


@pytest.mark.asyncio
async def test_html_identity_applied():
    """Cores do cliente devem estar no CSS global de cada slide."""
    agent = VisualSpecAgent(provider=FakeLLMProvider())
    client = _make_client(VisualStyle.CLEAN)  # accent = #c9a55c
    niche_ctx = _make_niche_context()
    copies = _make_copies(2)

    spec = await agent.generate(client=client, niche_context=niche_ctx, copies=copies)
    renderer = HTMLRenderer()

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        html_paths = await renderer.render(spec, out)
        for path in html_paths:
            html = path.read_text()
            assert "#c9a55c" in html  # accent do cliente
            assert "#0c2137" in html  # primary do cliente
