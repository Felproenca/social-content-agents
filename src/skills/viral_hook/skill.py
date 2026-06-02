from src.core.skill import Skill, SkillInput, SkillOutput

HOOK_TEMPLATES = {
    "curiosity": "O que {pct}% dos {audience} não sabem sobre {topic}",
    "pain": "Se você luta com {topic}, este post é para você.",
    "data": "{pct}% das pessoas erram em {topic}. Aqui está o porquê.",
    "controversy": "Pare de seguir o conselho popular sobre {topic}. Faça isso.",
    "story": "Há 1 ano eu não sabia nada sobre {topic}. Hoje isso mudou tudo.",
    "challenge": "Testei {topic} por 30 dias. O resultado me surpreendeu.",
}


class ViralHookInput(SkillInput):
    topic: str
    platform: str = "linkedin"
    hook_type: str = "curiosity"
    audience: str = "profissionais"


class ViralHookOutput(SkillOutput):
    hooks: list[str] = []
    best_hook: str = ""
    hook_type_used: str = ""


class ViralHookSkill(Skill):
    name = "viral_hook"
    description = "Gera ganchos virais para abertura de conteúdo em redes sociais."

    async def run(self, input: ViralHookInput) -> ViralHookOutput:  # type: ignore[override]
        hooks = []
        for hook_type, template in HOOK_TEMPLATES.items():
            try:
                hook = template.format(
                    topic=input.topic,
                    audience=input.audience,
                    pct=97 if "curiosity" in hook_type else 73,
                )
            except KeyError:
                hook = template
            hooks.append(hook)

        best_hook = HOOK_TEMPLATES.get(input.hook_type, hooks[0]).format(
            topic=input.topic,
            audience=input.audience,
            pct=97,
        )

        return ViralHookOutput(
            hooks=hooks,
            best_hook=best_hook,
            hook_type_used=input.hook_type,
        )

    def input_schema(self) -> dict:
        return ViralHookInput.model_json_schema()
