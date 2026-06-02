from typing import Any
from src.core.skill import Skill, SkillInput, SkillOutput


class AnalyticsInsightsInput(SkillInput):
    metrics: list[dict[str, Any]] = []
    period: str = "last_30_days"


class AnalyticsInsightsOutput(SkillOutput):
    top_posts: list[dict[str, Any]] = []
    worst_posts: list[dict[str, Any]] = []
    patterns: dict[str, Any] = {}
    recommendations: list[str] = []
    engagement_rate_avg: float = 0.0


def _engagement_rate(m: dict[str, Any]) -> float:
    reach = m.get("reach", 1) or 1
    interactions = (
        m.get("likes", 0)
        + m.get("comments", 0)
        + m.get("shares", 0)
        + m.get("saves", 0)
    )
    return round(interactions / reach * 100, 2)


class AnalyticsInsightsSkill(Skill):
    name = "analytics_insights"
    description = "Extrai insights acionáveis de métricas de publicações."

    async def run(self, input: AnalyticsInsightsInput) -> AnalyticsInsightsOutput:  # type: ignore[override]
        if not input.metrics:
            return AnalyticsInsightsOutput(
                recommendations=["Ainda sem dados históricos. Publique e colete métricas."]
            )

        scored = sorted(input.metrics, key=_engagement_rate, reverse=True)
        avg = sum(_engagement_rate(m) for m in scored) / len(scored)

        top = scored[:3]
        worst = scored[-3:]

        recs = [
            f"Replique o formato dos top posts: {[m.get('post_id', '?') for m in top]}",
            "Evite os padrões dos posts com menor engajamento.",
            "Priorize horários com maior alcance histórico.",
        ]

        return AnalyticsInsightsOutput(
            top_posts=top,
            worst_posts=worst,
            patterns={"avg_engagement_rate": avg},
            recommendations=recs,
            engagement_rate_avg=avg,
        )

    def input_schema(self) -> dict:
        return AnalyticsInsightsInput.model_json_schema()
