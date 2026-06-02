import json
from src.core.agent import Agent, AgentContext, AgentResult


class ResearchAgent(Agent):
    name = "ResearchAgent"
    role = "Pesquisador de conteúdo especializado"
    goal = (
        "Coletar informações relevantes, fontes confiáveis e contexto suficiente "
        "sobre um tópico para embasar a criação de conteúdo."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Pesquise o tópico: '{context.topic}'\n"
                    f"Plataforma-alvo: {context.platform or 'geral'}\n"
                    f"Audiência: {context.audience or 'profissionais'}\n\n"
                    "Retorne um JSON com:\n"
                    "- key_points: lista dos 5 pontos mais relevantes\n"
                    "- angles: 3 ângulos de abordagem diferentes\n"
                    "- data_points: estatísticas ou fatos de impacto (invente dados plausíveis se necessário)\n"
                    "- keywords: palavras-chave SEO relevantes\n"
                    "- sources_suggested: tipos de fontes a consultar"
                ),
            }
        ]
        response = await self._chat(messages, system=self._system_prompt(), use_tools=False)
        raw = response.content[0].text

        try:
            # Extract JSON if wrapped in markdown code block
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            output = json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            output = {"raw": raw}

        self.memory.add("assistant", raw)
        return AgentResult(agent=self.name, success=True, output=output)
