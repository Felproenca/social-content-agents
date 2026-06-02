import json
from src.core.agent import Agent, AgentContext, AgentResult


class ProspectingAgent(Agent):
    name = "ProspectingAgent"
    role = "Especialista em audiência e prospecção digital"
    goal = (
        "Identificar segmentos de audiência ideais, dores e desejos específicos, "
        "e oportunidades de conexão entre o conteúdo e potenciais clientes/seguidores."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        research = context.metadata.get("ResearchAgent", {})
        messages = [
            {
                "role": "user",
                "content": (
                    f"Tópico: '{context.topic}'\n"
                    f"Plataforma: {context.platform or 'geral'}\n"
                    f"Audiência base: {context.audience or 'não definida'}\n"
                    f"Pesquisa: {json.dumps(research, ensure_ascii=False)}\n\n"
                    "Mapeie a audiência ideal. Retorne JSON com:\n"
                    "- personas: lista de 3 personas com nome, cargo, dores e objetivos\n"
                    "- segments: segmentos de audiência a alcançar\n"
                    "- pain_points: principais dores relacionadas ao tópico\n"
                    "- desire_triggers: gatilhos de desejo para cada segmento\n"
                    "- engagement_hooks: formas de iniciar conversa com cada persona\n"
                    "- opportunity_score: 1-10 de oportunidade de negócio neste tópico"
                ),
            }
        ]
        response = await self._chat(messages, system=self._system_prompt(), use_tools=False)
        raw = response.content[0].text

        try:
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            output = json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            output = {"raw": raw}

        return AgentResult(agent=self.name, success=True, output=output)
