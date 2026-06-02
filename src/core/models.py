"""Domain models — dataclasses compartilhados entre agentes e skills."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Niche models ──────────────────────────────────────────────────────────────

class TopicMaturity(Enum):
    EMERGENTE  = "emergente"
    ASCENDENDO = "ascendendo"
    MAINSTREAM = "mainstream"
    SATURADO   = "saturado"


class EditorialPosition(Enum):
    PROVOCACAO   = "provocacao"
    EDUCACAO     = "educacao"
    OPINIAO      = "opiniao"
    DEMONSTRACAO = "demonstracao"


@dataclass
class NicheLanguage:
    usa: list[str]
    evita: list[str]
    tom: str
    nivel_tecnico: str


@dataclass
class NicheProfile:
    """Perfil completo de um nicho. Salvo em data/niches/[slug].json"""
    nicho: str
    slug: str
    descricao: str
    audiencia_primaria: str
    audiencia_secundaria: str
    linguagem: NicheLanguage
    temas_evergreen: list[str]
    temas_trend: list[str]
    angulos_inexplorados: list[str]
    cliches_a_evitar: list[str]
    referencias_setor: list[str]
    posicoes_editoriais: list[str]
    gatilhos_emocionais: dict[str, str]
    formato_por_plataforma: dict[str, str]
    source: str = "descoberto"
    updated_at: str = ""
    performance_data: dict = field(default_factory=dict)


@dataclass
class NicheContext:
    """Contexto gerado pelo NicheIntelligenceAgent para cada conteúdo."""
    angulo: str
    linguagem: NicheLanguage
    posicao: EditorialPosition
    o_que_evitar: list[str]
    referencias: list[str]
    tendencia_status: TopicMaturity
    hook_direction: str
    insights_exclusivos: list[str]


@dataclass
class NicheInput:
    nicho: str
    objetivo: str
    plataforma: str
    tema: Optional[str] = None
    contexto_cliente: dict = field(default_factory=dict)


# ── Visual models ─────────────────────────────────────────────────────────────

class VisualStyle(Enum):
    CLEAN     = "clean"      # muito espaço, elegante, premium
    DARK      = "dark"       # fundo escuro, contraste alto
    BOLD      = "bold"       # tipografia grande, impacto direto
    EDITORIAL = "editorial"  # estilo revista, foto + texto
    TECHNICAL = "technical"  # grid, monospace, dados, terminal
    WARM      = "warm"       # cores quentes, humano, próximo


class VisualType(Enum):
    TIPOGRAFICO = "tipografico"  # só texto, tipografia como design
    FOTO_TEXTO  = "foto_texto"   # foto real + texto sobreposto
    SCREENSHOT  = "screenshot"   # tela real, terminal, sistema
    DADOS       = "dados"        # gráfico, número grande, métrica
    HIBRIDO     = "hibrido"      # combinação conforme o slide


class SlideRole(Enum):
    GANCHO   = "gancho"    # slide 1 — para o scroll
    CONTEUDO = "conteudo"  # slides 2-N — entrega valor
    PROVA    = "prova"     # dado, número, caso real
    CTA      = "cta"       # último slide — próximo passo


@dataclass
class ClientPalette:
    primary:    str
    secondary:  str
    accent:     str
    background: str
    text:       str
    text_light: str


@dataclass
class ClientTypography:
    heading: str
    body:    str
    mono:    str = "Syne Mono"


@dataclass
class ClientContext:
    slug:       str
    name:       str
    palette:    ClientPalette
    typography: ClientTypography
    style:      VisualStyle
    logo_url:   Optional[str] = None
    nicho:      str = ""


@dataclass
class SlideSpec:
    role:                 SlideRole
    slide_number:         int
    total_slides:         int
    headline:             str
    body:                 Optional[str]
    visual_type:          VisualType
    layout:               str   # center | left | split | overlay
    focal_point:          str
    emphasis:             list[str]
    cta:                  Optional[str]
    background_treatment: str   # solid | gradient | grain | image


@dataclass
class VisualSpec:
    client:        ClientContext
    niche_context: NicheContext
    style:         VisualStyle
    visual_type:   VisualType
    mood:          str
    format:        str           # 1:1 | 4:5 | 9:16
    slides:        list[SlideSpec]
    global_css:    str

