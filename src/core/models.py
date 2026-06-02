"""Domain models — dataclasses compartilhados entre agentes e skills."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TopicMaturity(Enum):
    EMERGENTE  = "emergente"   # poucos falam, alto valor
    ASCENDENDO = "ascendendo"  # crescendo, janela aberta
    MAINSTREAM = "mainstream"  # todo mundo fala
    SATURADO   = "saturado"    # evitar ou subverter


class EditorialPosition(Enum):
    PROVOCACAO   = "provocacao"   # desafiar o consenso
    EDUCACAO     = "educacao"     # ensinar o que poucos sabem
    OPINIAO      = "opiniao"      # tomar partido com argumento
    DEMONSTRACAO = "demonstracao" # mostrar ao vivo, não explicar


@dataclass
class NicheLanguage:
    usa: list[str]      # termos de especialista sênior
    evita: list[str]    # clichês que desposicionam
    tom: str            # como fala um sênior deste nicho
    nivel_tecnico: str  # iniciante / praticante / especialista


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
    gatilhos_emocionais: dict[str, str]     # medo, ganancia, status, curiosidade
    formato_por_plataforma: dict[str, str]
    source: str = "descoberto"              # descoberto | manual | atualizado
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
    objetivo: str        # awareness | autoridade | conversao
    plataforma: str      # instagram | linkedin | tiktok | youtube
    tema: Optional[str] = None
    contexto_cliente: dict = field(default_factory=dict)
