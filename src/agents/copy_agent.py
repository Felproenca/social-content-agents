import json
from src.core.agent import Agent, AgentContext, AgentResult

COPY_SYSTEM_PROMPT = """
Você é um criador de conteúdo sênior especializado em {nicho}.

Não é um generalista. Você tem ponto de vista.
Você sabe o que está emergindo antes de virar mainstream.
Você tem opinião sobre o que outros evitam opinar.

Contexto de nicho:
  Ângulo único: {angulo}
  Linguagem — usa: {usa}
  Linguagem — evita: {evita}
  Tom: {tom}
  Posição editorial: {posicao}
  Direção do gancho: {hook_direction}
  O que NÃO dizer: {o_que_evitar}

Princípio dos 15% e 85%:

Para os 15% que decidem pela emoção:
  A primeira frase para o scroll — não explica, provoca
  Começa na dor ou no desejo real
  Nunca começa pelo produto ou pela tecnologia

Para os 85% que precisam de validação:
  Prova concreta depois da emoção
  Resultado específico — não promessa genérica
  Lógica que justifica a decisão que o coração já tomou

NUNCA gerar conteúdo que:
  Poderia ser de qualquer marca do setor
  Descreve tecnologia antes de conectar com o problema
  Usa palavras da lista evita
  É bom mas não tem ponto de vista
  Começa pelo produto ou pelo serviço
"""

GENERIC_SYSTEM_PROMPT = """
Você é um redator especialista em conteúdo para redes sociais.
Crie conteúdo de alta conversão adaptado à plataforma e ao tom de voz solicitado.
Responda sempre em português do Brasil.
"""


class CopyAgent(Agent):
    name = "CopyAgent"
    role = "Redator especialista em conteúdo para redes sociais"
    goal = (
        "Criar variações de copy de alta conversão, adaptadas ao tom de voz, "
        "às características de cada plataforma e ao contexto de nicho fornecido."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        research = context.metadata.get("ResearchAgent", {})
        trends = context.metadata.get("TrendAgent", {})
        niche_data = context.metadata.get("NicheIntelligenceAgent", {})
        variations = context.metadata.get("copy_variations", 3)

        system = self._build_system(niche_data, context.topic)

        user_msg = (
            f"Tópico: '{context.topic}'\n"
            f"Plataforma: {context.platform or 'geral'}\n"
            f"Tom: {context.tone}\n"
            f"Audiência: {context.audience or 'profissionais'}\n"
            f"Pesquisa: {json.dumps(research, ensure_ascii=False)}\n"
            f"Tendências: {json.dumps(trends, ensure_ascii=False)}\n"
        )

        if niche_data:
            user_msg += (
                f"Insights exclusivos do nicho: "
                f"{json.dumps(niche_data.get('insights_exclusivos', []), ensure_ascii=False)}\n"
            )

        user_msg += (
            f"\nCrie {variations} variações de copy completas para "
            f"{context.platform or 'redes sociais'}.\n"
            "Retorne JSON com uma lista 'copies', cada item contendo:\n"
            "- hook: gancho de abertura (primeira linha impactante)\n"
            "- body: corpo do conteúdo\n"
            "- cta: call-to-action\n"
            "- hashtags: lista de hashtags sugeridas\n"
            "- format: formato recomendado (post, carrossel, reel, thread...)\n"
            "- estimated_read_time: tempo estimado de leitura em segundos\n"
            "- angulo_usado: o ângulo editorial aplicado nesta variação"
        )

        messages = [{"role": "user", "content": user_msg}]
        response = await self._chat(messages, system=system, use_tools=False)
        raw = response.content[0].text

        try:
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            output = json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            output = {"raw": raw}

        return AgentResult(agent=self.name, success=True, output=output)

    def _build_system(self, niche_data: dict, topic: str) -> str:
        if not niche_data:
            return GENERIC_SYSTEM_PROMPT

        return COPY_SYSTEM_PROMPT.format(
            nicho=topic,
            angulo=niche_data.get("angulo", "ângulo único do nicho"),
            usa=niche_data.get("linguagem", {}).get("usa", []),
            evita=niche_data.get("linguagem", {}).get("evita", []),
            tom=niche_data.get("linguagem", {}).get("tom", "profissional"),
            posicao=niche_data.get("posicao", "educacao"),
            hook_direction=niche_data.get("hook_direction", ""),
            o_que_evitar=niche_data.get("o_que_evitar", []),
        )
