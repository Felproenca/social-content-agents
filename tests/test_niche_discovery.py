"""
Testa NicheDiscoverySkill com 3 cenários:
  - nicho conhecido (carregado do cache)
  - nicho parcialmente conhecido
  - nicho completamente novo (descoberto via LLM)
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.core.llm import LLMResponse, LLMProvider
from src.core.models import NicheProfile
from src.skills.niche_discovery import NicheDiscoverySkill


# ── Fake LLM provider ─────────────────────────────────────────────────────────

class FakeLLMProvider(LLMProvider):
    def __init__(self, response_text: str):
        self._response = response_text

    async def chat(self, messages, system=None, max_tokens=4096):
        return LLMResponse(self._response)


def _fake_profile_json(nicho: str, slug: str) -> str:
    return json.dumps({
        "nicho": nicho,
        "slug": slug,
        "descricao": f"Descrição de {nicho}",
        "audiencia_primaria": "Empresas do setor",
        "audiencia_secundaria": "Fornecedores",
        "linguagem": {
            "usa": ["termo1", "termo2", "termo3"],
            "evita": ["cliche1", "cliche2"],
            "tom": "direto e técnico",
            "nivel_tecnico": "especialista",
        },
        "temas_evergreen": ["Tema A", "Tema B", "Tema C"],
        "temas_trend": ["Tendência X 2026", "Mudança Y"],
        "angulos_inexplorados": ["Ângulo oculto 1", "Ângulo oculto 2"],
        "cliches_a_evitar": ["Frase batida 1", "Frase batida 2"],
        "referencias_setor": ["Referência 1"],
        "posicoes_editoriais": ["Posição A", "Posição B"],
        "gatilhos_emocionais": {
            "medo": "Perder mercado",
            "ganancia": "Aumentar margem",
            "status": "Ser reconhecido como líder",
            "curiosidade": "O que os top players fazem diferente",
        },
        "formato_por_plataforma": {
            "linkedin": "Artigo longo com dados",
            "instagram": "Carrossel visual",
        },
    })


# ── Slug generation ────────────────────────────────────────────────────────────

def test_slug_simples():
    skill = NicheDiscoverySkill(llm=FakeLLMProvider(""))
    assert skill._to_slug("Inteligência Artificial") == "inteligencia-artificial"


def test_slug_com_caracteres_especiais():
    skill = NicheDiscoverySkill(llm=FakeLLMProvider(""))
    assert skill._to_slug("Pet Shop & Cia") == "pet-shop-cia"


def test_slug_nicho_composto():
    skill = NicheDiscoverySkill(llm=FakeLLMProvider(""))
    assert skill._to_slug("Escola de Mergulho") == "escola-de-mergulho"


# ── Cache hit: nicho já conhecido ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_carrega_perfil_existente():
    """Nicho já descoberto — deve carregar do JSON sem chamar o LLM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        niches_dir = Path(tmpdir)
        slug = "inteligencia-artificial"
        profile_path = niches_dir / f"{slug}.json"
        profile_path.write_text(_fake_profile_json("inteligência artificial", slug))

        provider = FakeLLMProvider("não deveria ser chamado")
        skill = NicheDiscoverySkill(llm=provider)
        skill.__class__  # monkeypatch NICHES_DIR

        with patch("src.skills.niche_discovery.NICHES_DIR", niches_dir):
            profile = await skill.discover("inteligência artificial")

    assert isinstance(profile, NicheProfile)
    assert profile.nicho == "inteligência artificial"
    assert profile.slug == slug
    assert len(profile.linguagem.usa) >= 1


# ── Cache miss: nicho novo — descoberta via LLM ────────────────────────────────

@pytest.mark.asyncio
async def test_descobre_nicho_novo():
    """Nicho nunca visto — deve chamar o LLM e salvar o JSON."""
    nicho = "distribuidora de alimentos"
    slug = "distribuidora-de-alimentos"
    fake_json = _fake_profile_json(nicho, slug)

    with tempfile.TemporaryDirectory() as tmpdir:
        niches_dir = Path(tmpdir)
        provider = FakeLLMProvider(fake_json)
        skill = NicheDiscoverySkill(llm=provider)

        with patch("src.skills.niche_discovery.NICHES_DIR", niches_dir):
            profile = await skill.discover(nicho)
            saved_path = niches_dir / f"{slug}.json"

            assert isinstance(profile, NicheProfile)
            assert profile.nicho == nicho
            assert saved_path.exists(), "Perfil deve ser salvo em disco"
            saved = json.loads(saved_path.read_text())
            assert saved["source"] == "descoberto"
            assert saved["updated_at"] != ""


# ── Nicho completamente incomum ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nicho_incomum():
    """Escola de mergulho — sistema não conhece, deve descobrir sem erro."""
    nicho = "escola de mergulho"
    slug = "escola-de-mergulho"
    fake_json = _fake_profile_json(nicho, slug)

    with tempfile.TemporaryDirectory() as tmpdir:
        niches_dir = Path(tmpdir)
        provider = FakeLLMProvider(fake_json)
        skill = NicheDiscoverySkill(llm=provider)

        with patch("src.skills.niche_discovery.NICHES_DIR", niches_dir):
            profile = await skill.discover(nicho)

    assert profile.nicho == nicho
    assert profile.slug == slug


# ── Loop de aprendizado ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_from_performance_alto_engajamento():
    """Post com engajamento alto deve adicionar ângulo aos temas_trend."""
    nicho = "marketing digital"
    slug = "marketing-digital"
    fake_json = _fake_profile_json(nicho, slug)

    with tempfile.TemporaryDirectory() as tmpdir:
        niches_dir = Path(tmpdir)
        profile_path = niches_dir / f"{slug}.json"
        profile_path.write_text(fake_json)

        skill = NicheDiscoverySkill(llm=FakeLLMProvider(""))

        with patch("src.skills.niche_discovery.NICHES_DIR", niches_dir):
            await skill.update_from_performance(
                slug=slug,
                post_data={"angulo": "ROI real vs ROI relatado", "hook_type": "dado_inesperado"},
                metrics={"engagement_rate": 0.15},  # 5x acima do benchmark de 3%
            )
            updated = json.loads(profile_path.read_text())

    assert "ROI real vs ROI relatado" in updated["temas_trend"]


@pytest.mark.asyncio
async def test_update_from_performance_baixo_engajamento():
    """Post com engajamento baixo deve marcar tema como clichê."""
    nicho = "vendas b2b"
    slug = "vendas-b2b"
    fake_json = _fake_profile_json(nicho, slug)

    with tempfile.TemporaryDirectory() as tmpdir:
        niches_dir = Path(tmpdir)
        profile_path = niches_dir / f"{slug}.json"
        profile_path.write_text(fake_json)

        skill = NicheDiscoverySkill(llm=FakeLLMProvider(""))

        with patch("src.skills.niche_discovery.NICHES_DIR", niches_dir):
            await skill.update_from_performance(
                slug=slug,
                post_data={"tema": "pipeline de vendas", "hook_type": "curiosity"},
                metrics={"engagement_rate": 0.005},  # abaixo de 50% do benchmark
            )
            updated = json.loads(profile_path.read_text())

    assert any("pipeline de vendas" in c for c in updated["cliches_a_evitar"])
