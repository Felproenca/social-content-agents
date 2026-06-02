import json
from typing import Any
from src.core.agent import Agent, AgentContext, AgentResult


class PerformanceAgent(Agent):
    name = "PerformanceAgent"
    role = "Analista de performance e otimização de conteúdo"
    goal = (
        "Analisar métricas de publicações anteriores, identificar padrões de sucesso "
        "e gerar recomendações para melhorar o desempenho das próximas criações."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        metrics: list[dict[str, Any]] = context.metadata.get("metrics", [])
        copies = context.metadata.get("CopyAgent", {}).get("copies", [])

        messages = [
            {
                "role": "user",
                "content": (
                    f"Tópico atual: '{context.topic}'\n"
                    f"Plataforma: {context.platform or 'geral'}\n"
                    f"Métricas históricas disponíveis: {json.dumps(metrics, ensure_ascii=False)}\n"
                    f"Copies geradas: {json.dumps(copies, ensure_ascii=False)}\n\n"
                    "Analise e otimize. Retorne JSON com:\n"
                    "- performance_score: pontuação estimada de 1-100 para cada copy\n"
                    "- top_performer: índice da copy com maior potencial\n"
                    "- improvements: lista de melhorias específicas por copy\n"
                    "- ab_test_suggestion: sugestão de teste A/B entre 2 variações\n"
                    "- predicted_metrics: estimativa de alcance, engajamento e cliques\n"
                    "- learnings: aprendizados do histórico para aplicar agora"
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
