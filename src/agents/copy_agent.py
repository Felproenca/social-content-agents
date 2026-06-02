import json
from src.core.agent import Agent, AgentContext, AgentResult


class CopyAgent(Agent):
    name = "CopyAgent"
    role = "Redator especialista em conteúdo para redes sociais"
    goal = (
        "Criar variações de copy de alta conversão, adaptadas ao tom de voz "
        "e às características de cada plataforma."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        research = context.metadata.get("ResearchAgent", {})
        trends = context.metadata.get("TrendAgent", {})
        variations = context.metadata.get("copy_variations", 3)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Tópico: '{context.topic}'\n"
                    f"Plataforma: {context.platform or 'geral'}\n"
                    f"Tom: {context.tone}\n"
                    f"Audiência: {context.audience or 'profissionais'}\n"
                    f"Pesquisa: {json.dumps(research, ensure_ascii=False)}\n"
                    f"Tendências: {json.dumps(trends, ensure_ascii=False)}\n\n"
                    f"Crie {variations} variações de copy completas para {context.platform or 'redes sociais'}.\n"
                    "Retorne JSON com uma lista 'copies', cada item contendo:\n"
                    "- hook: gancho de abertura (primeira linha impactante)\n"
                    "- body: corpo do conteúdo\n"
                    "- cta: call-to-action\n"
                    "- hashtags: lista de hashtags sugeridas\n"
                    "- format: formato recomendado (post, carrossel, reel, thread...)\n"
                    "- estimated_read_time: tempo estimado de leitura em segundos"
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
