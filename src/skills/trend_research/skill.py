from src.core.skill import Skill, SkillInput, SkillOutput


class TrendResearchInput(SkillInput):
    topic: str
    platform: str = "linkedin"
    timeframe: str = "last_week"


class TrendResearchOutput(SkillOutput):
    trends: list[str] = []
    hashtags: list[str] = []
    content_formats: list[str] = []
    competitor_insights: str = ""


class TrendResearchSkill(Skill):
    name = "trend_research"
    description = "Identifica tendências de conteúdo por plataforma e nicho."

    async def run(self, input: TrendResearchInput) -> TrendResearchOutput:  # type: ignore[override]
        # Stub: in production, integrate with Google Trends, BuzzSumo, etc.
        return TrendResearchOutput(
            trends=[f"Tendência sobre {input.topic} em {input.platform}"],
            hashtags=[f"#{input.topic.replace(' ', '')}", f"#{input.platform}"],
            content_formats=["carrossel", "vídeo curto", "artigo longo"],
            competitor_insights="Integrar com APIs externas para dados reais.",
        )

    def input_schema(self) -> dict:
        return TrendResearchInput.model_json_schema()
