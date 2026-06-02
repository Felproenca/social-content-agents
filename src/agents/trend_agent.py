import json
from src.core.agent import Agent, AgentContext, AgentResult


class TrendAgent(Agent):
    name = "TrendAgent"
    role = "Analista de tendências digitais"
    goal = (
        "Identificar tendências atuais, formatos virais e padrões de engajamento "
        "relevantes para o tópico e plataforma alvo."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        research = context.metadata.get("ResearchAgent", {})
        messages = [
            {
                "role": "user",
                "content": (
                    f"Tópico: '{context.topic}'\n"
                    f"Plataforma: {context.platform or 'geral'}\n"
                    f"Pesquisa prévia: {json.dumps(research, ensure_ascii=False)}\n\n"
                    "Identifique tendências atuais. Retorne JSON com:\n"
                    "- trending_formats: formatos de conteúdo em alta (ex: carrossel, reel, thread)\n"
                    "- viral_patterns: padrões que estão gerando alto engajamento\n"
                    "- best_posting_times: melhores horários por dia da semana\n"
                    "- hashtags: 10 hashtags relevantes e em alta\n"
                    "- content_gap: o que ainda não foi explorado sobre o tópico"
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
