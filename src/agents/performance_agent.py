import json
from typing import Any

from src.core.agent import Agent, AgentContext, AgentResult
from src.skills.niche_discovery import NicheDiscoverySkill


class PerformanceAgent(Agent):
    name = "PerformanceAgent"
    role = "Analista de performance e otimização de conteúdo"
    goal = (
        "Analisar métricas de publicações anteriores, identificar padrões de sucesso "
        "e gerar recomendações para melhorar o desempenho das próximas criações."
    )

    def __init__(self, discovery: NicheDiscoverySkill | None = None, **kwargs):
        super().__init__(**kwargs)
        self.discovery = discovery

    async def run(self, context: AgentContext) -> AgentResult:
        metrics: list[dict[str, Any]] = context.metadata.get("metrics", [])
        copies = context.metadata.get("CopyAgent", {}).get("copies", [])
        niche_data = context.metadata.get("NicheIntelligenceAgent", {})

        user_msg = (
            f"Tópico atual: '{context.topic}'\n"
            f"Plataforma: {context.platform or 'geral'}\n"
            f"Métricas históricas disponíveis: {json.dumps(metrics, ensure_ascii=False)}\n"
            f"Copies geradas: {json.dumps(copies, ensure_ascii=False)}\n"
        )

        if niche_data:
            user_msg += (
                f"Ângulo aplicado: {niche_data.get('angulo', '')}\n"
                f"Posição editorial: {niche_data.get('posicao', '')}\n"
            )

        user_msg += (
            "\nAnalise e otimize. Retorne JSON com:\n"
            "- performance_score: pontuação estimada de 1-100 para cada copy\n"
            "- top_performer: índice da copy com maior potencial\n"
            "- improvements: lista de melhorias específicas por copy\n"
            "- ab_test_suggestion: sugestão de teste A/B entre 2 variações\n"
            "- predicted_metrics: estimativa de alcance, engajamento e cliques\n"
            "- learnings: aprendizados do histórico para aplicar agora"
        )

        messages = [{"role": "user", "content": user_msg}]
        response = await self._chat(messages, system=self._system_prompt(), use_tools=False)
        raw = response.content[0].text

        try:
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            output = json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            output = {"raw": raw}

        return AgentResult(agent=self.name, success=True, output=output)

    async def process_and_learn(
        self,
        post_data: dict,
        metrics: dict,
        nicho_slug: str,
    ) -> None:
        """
        Fecha o loop de aprendizado: atualiza o perfil do nicho com
        dados reais de performance após publicação e medição.
        """
        if self.discovery is None:
            return

        # Atualizar perfil do nicho com o que funcionou (ou não)
        await self.discovery.update_from_performance(
            slug=nicho_slug,
            post_data=post_data,
            metrics=metrics,
        )
