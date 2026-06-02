from src.core.skill import Skill, SkillInput, SkillOutput

PLATFORM_LIMITS = {
    "linkedin": 3000,
    "instagram": 2200,
    "tiktok": 2200,
    "x_twitter": 280,
    "youtube": 5000,
}


class PlatformFormatterInput(SkillInput):
    copy: str
    platform: str = "linkedin"
    include_emojis: bool = False
    include_hashtags: bool = True
    hashtags: list[str] = []


class PlatformFormatterOutput(SkillOutput):
    formatted_copy: str = ""
    char_count: int = 0
    within_limits: bool = True


class PlatformFormatterSkill(Skill):
    name = "platform_formatter"
    description = "Formata copy para as regras e limites de cada plataforma."

    async def run(self, input: PlatformFormatterInput) -> PlatformFormatterOutput:  # type: ignore[override]
        text = input.copy
        limit = PLATFORM_LIMITS.get(input.platform, 2200)

        if input.include_hashtags and input.hashtags:
            hashtag_str = " ".join(
                h if h.startswith("#") else f"#{h}" for h in input.hashtags
            )
            text = f"{text}\n\n{hashtag_str}"

        # Truncate to platform limit if needed
        if len(text) > limit:
            text = text[: limit - 3] + "..."

        return PlatformFormatterOutput(
            formatted_copy=text,
            char_count=len(text),
            within_limits=len(text) <= limit,
        )

    def input_schema(self) -> dict:
        return PlatformFormatterInput.model_json_schema()
