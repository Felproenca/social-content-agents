from src.core.skill import Skill, SkillInput, SkillOutput

PLATFORM_DIMENSIONS = {
    "instagram": "1080x1080",
    "linkedin": "1200x627",
    "tiktok": "1080x1920",
    "youtube": "1280x720",
    "x_twitter": "1200x675",
}


class DesignPromptInput(SkillInput):
    concept: str
    style: str = "photorealistic"
    platform: str = "instagram"
    mood: str = "professional"
    brand_colors: str = ""


class DesignPromptOutput(SkillOutput):
    prompt_en: str = ""
    negative_prompt: str = ""
    dimensions: str = ""
    style_suffix: str = ""


class DesignPromptSkill(Skill):
    name = "design_prompt"
    description = "Gera prompts visuais otimizados para ferramentas de IA (Midjourney, DALL-E, Flux)."

    async def run(self, input: DesignPromptInput) -> DesignPromptOutput:  # type: ignore[override]
        dims = PLATFORM_DIMENSIONS.get(input.platform, "1080x1080")
        w, h = dims.split("x")
        ar_w, ar_h = int(w) // 270, int(h) // 270  # simplify ratio

        prompt = (
            f"{input.concept}, {input.style} style, {input.mood} mood, "
            f"professional composition, high quality, sharp focus, "
            f"{'color palette: ' + input.brand_colors if input.brand_colors else 'vibrant colors'}"
        )
        negative = "blur, watermark, text, logo, low quality, distorted, ugly, deformed"
        suffix = f"--ar {ar_w}:{ar_h} --v 6 --q 2"

        return DesignPromptOutput(
            prompt_en=prompt,
            negative_prompt=negative,
            dimensions=dims,
            style_suffix=suffix,
        )

    def input_schema(self) -> dict:
        return DesignPromptInput.model_json_schema()
