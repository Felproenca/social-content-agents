"""
NicheIntelligenceAgent

Recebe o perfil do nicho (descoberto ou carregado)
e gera o contexto de especialista sênior para cada conteúdo.

Não é o mesmo contexto para todos os posts.
Para cada tema + objetivo + plataforma, o ângulo é único.
"""

from src.core.agent import Agent, AgentContext, AgentResult
from src.core.models import (
    EditorialPosition,
    NicheContext,
    NicheInput,
    NicheProfile,
    TopicMaturity,
)
from src.skills.niche_discovery import NicheDiscoverySkill

MATURITY_PROMPT = """
Dado o perfil do nicho {nicho} e o tema "{tema}",
classifique a maturidade deste tema:

Perfil do nicho:
- Temas trend atuais: {temas_trend}
- Temas evergreen: {temas_evergreen}
- Ângulos inexplorados: {angulos_inexplorados}

Classificações possíveis:
- EMERGENTE: poucos falam, alto valor para quem explorar agora
- ASCENDENDO: crescendo, janela ainda aberta
- MAINSTREAM: todo mundo fala, precisa de ângulo diferente
- SATURADO: overdiscutido, só vale se subverter completamente

Retorne apenas a classificação e uma linha de justificativa.
"""

ANGLE_PROMPT = """
Nicho: {nicho}
Tema: {tema}
Maturidade: {maturidade}
Ângulos inexplorados do nicho: {angulos_inexplorados}
Objetivo do conteúdo: {objetivo}
Plataforma: {plataforma}

Se o tema é EMERGENTE:
  → Definir como surfar a tendência com autoridade
  → Não explicar o óbvio — ir mais fundo

Se o tema é ASCENDENDO:
  → Encontrar o ângulo que ninguém viu ainda dentro do tema
  → Pode ter posição contra o consenso emergente

Se o tema é MAINSTREAM ou SATURADO:
  → Encontrar o ângulo que contradiz ou subverte o mainstream
  → A verdade incômoda que os outros evitam
  → O contra-argumento que ninguém tem coragem de fazer

Retorne:
1. O ângulo único em uma frase
2. Por que este ângulo funciona neste nicho
3. O que a maioria faz que este ângulo evita
"""

HOOK_DIRECTION_MAP = {
    EditorialPosition.PROVOCACAO:   "Começa com a afirmação que desafia — não com a pergunta",
    EditorialPosition.EDUCACAO:     "Começa com o que a pessoa não sabe que não sabe",
    EditorialPosition.OPINIAO:      "Começa com a posição — não com a contextualização",
    EditorialPosition.DEMONSTRACAO: "Começa com o resultado — não com o processo",
}

POSITION_MATRIX: dict[tuple, EditorialPosition] = {
    ("awareness",  TopicMaturity.EMERGENTE):  EditorialPosition.EDUCACAO,
    ("awareness",  TopicMaturity.ASCENDENDO): EditorialPosition.OPINIAO,
    ("awareness",  TopicMaturity.MAINSTREAM): EditorialPosition.PROVOCACAO,
    ("awareness",  TopicMaturity.SATURADO):   EditorialPosition.PROVOCACAO,
    ("autoridade", TopicMaturity.EMERGENTE):  EditorialPosition.DEMONSTRACAO,
    ("autoridade", TopicMaturity.ASCENDENDO): EditorialPosition.OPINIAO,
    ("autoridade", TopicMaturity.MAINSTREAM): EditorialPosition.PROVOCACAO,
    ("autoridade", TopicMaturity.SATURADO):   EditorialPosition.PROVOCACAO,
    ("conversao",  TopicMaturity.EMERGENTE):  EditorialPosition.DEMONSTRACAO,
    ("conversao",  TopicMaturity.ASCENDENDO): EditorialPosition.DEMONSTRACAO,
    ("conversao",  TopicMaturity.MAINSTREAM): EditorialPosition.DEMONSTRACAO,
    ("conversao",  TopicMaturity.SATURADO):   EditorialPosition.PROVOCACAO,
}


class NicheIntelligenceAgent(Agent):
    name = "NicheIntelligenceAgent"
    role = "Estrategista de conteúdo especializado em inteligência de nicho"
    goal = (
        "Gerar o contexto de especialista sênior para qualquer nicho — "
        "ângulo único, linguagem correta, posição editorial clara."
    )

    def __init__(self, discovery: NicheDiscoverySkill, **kwargs):
        super().__init__(**kwargs)
        self.discovery = discovery

    async def run(self, context: AgentContext) -> AgentResult:
        niche_input = context.metadata.get("niche_input")
        if niche_input is None:
            niche_input = NicheInput(
                nicho=context.topic,
                objetivo=context.metadata.get("objetivo", "awareness"),
                plataforma=context.platform or "linkedin",
                tema=context.metadata.get("tema"),
            )

        niche_ctx = await self.process(niche_input)

        return AgentResult(
            agent=self.name,
            success=True,
            output={
                "angulo": niche_ctx.angulo,
                "posicao": niche_ctx.posicao.value,
                "hook_direction": niche_ctx.hook_direction,
                "tendencia_status": niche_ctx.tendencia_status.value,
                "o_que_evitar": niche_ctx.o_que_evitar,
                "insights_exclusivos": niche_ctx.insights_exclusivos,
                "linguagem": {
                    "usa": niche_ctx.linguagem.usa,
                    "evita": niche_ctx.linguagem.evita,
                    "tom": niche_ctx.linguagem.tom,
                    "nivel_tecnico": niche_ctx.linguagem.nivel_tecnico,
                },
                "_niche_context": niche_ctx,  # objeto completo para uso interno
            },
        )

    async def process(self, input: NicheInput) -> NicheContext:
        profile = await self.discovery.discover(input.nicho)
        maturidade = await self._classify_maturity(input.tema, profile)
        angulo = await self._find_angle(input, profile, maturidade)
        posicao = self._define_position(input.objetivo, maturidade)
        insights = self._select_insights(profile)

        return NicheContext(
            angulo=angulo,
            linguagem=profile.linguagem,
            posicao=posicao,
            o_que_evitar=profile.cliches_a_evitar,
            referencias=profile.referencias_setor,
            tendencia_status=maturidade,
            hook_direction=HOOK_DIRECTION_MAP[posicao],
            insights_exclusivos=insights,
        )

    async def _classify_maturity(
        self, tema: str | None, profile: NicheProfile
    ) -> TopicMaturity:
        if not tema:
            return TopicMaturity.EMERGENTE

        prompt = MATURITY_PROMPT.format(
            nicho=profile.nicho,
            tema=tema,
            temas_trend=profile.temas_trend[:5],
            temas_evergreen=profile.temas_evergreen[:5],
            angulos_inexplorados=profile.angulos_inexplorados[:3],
        )
        response = await self._provider.generate(
            system="Classifique a maturidade do tema. Seja preciso.",
            user=prompt,
            temperature=0.1,
        )
        upper = response.upper()
        for maturity in TopicMaturity:
            if maturity.value.upper() in upper:
                return maturity
        return TopicMaturity.ASCENDENDO

    async def _find_angle(
        self, input: NicheInput, profile: NicheProfile, maturidade: TopicMaturity
    ) -> str:
        prompt = ANGLE_PROMPT.format(
            nicho=profile.nicho,
            tema=input.tema or "tema livre",
            maturidade=maturidade.value,
            angulos_inexplorados=profile.angulos_inexplorados,
            objetivo=input.objetivo,
            plataforma=input.plataforma,
        )
        response = await self._provider.generate(
            system=(
                f"Você é especialista sênior em {profile.nicho}. "
                "Encontre o ângulo que ninguém viu ainda."
            ),
            user=prompt,
            temperature=0.4,
        )
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        return lines[0] if lines else response[:200]

    def _define_position(
        self, objetivo: str, maturidade: TopicMaturity
    ) -> EditorialPosition:
        return POSITION_MATRIX.get((objetivo, maturidade), EditorialPosition.EDUCACAO)

    def _select_insights(self, profile: NicheProfile) -> list[str]:
        best = profile.performance_data.get("best_angles", [])
        if best:
            return [b["angulo"] for b in best[:3]]
        return profile.angulos_inexplorados[:3]
