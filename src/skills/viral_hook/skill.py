from src.core.skill import Skill, SkillInput, SkillOutput

HOOK_TEMPLATES = {
    "provocacao": (
        "Pare de {topic}. {audience} que fazem isso estão cometendo o erro mais caro do setor."
    ),
    "dado_inesperado": (
        "{pct}% dos {audience} que apostam em {topic} não medem o que importa. "
        "Aqui está o número que eles ignoram."
    ),
    "confissao": (
        "Vou ser honesto: tudo que me ensinaram sobre {topic} estava errado. "
        "Aqui o que ninguém no setor admite."
    ),
    "pergunta_incomoda": (
        "Quanto {topic} custa de verdade — incluindo o que você nunca coloca na planilha?"
    ),
    "declaracao_com_posicao": (
        "{topic} não é sobre tecnologia. É sobre quem tem coragem de mudar de método primeiro."
    ),
    "curiosity": (
        "O que {pct}% dos {audience} não sabem sobre {topic} — e por que isso está custando caro."
    ),
}


class ViralHookInput(SkillInput):
    topic: str
    platform: str = "linkedin"
    hook_type: str = "provocacao"
    audience: str = "profissionais"
    # Campos de nicho (opcionais — enriquecem os ganchos quando disponíveis)
    angulo: str = ""
    posicao: str = ""
    hook_direction: str = ""
    cliches_a_evitar: list[str] = []
    maturidade: str = ""


class ViralHookOutput(SkillOutput):
    hooks: list[str] = []
    best_hook: str = ""
    hook_type_used: str = ""
    hook_direction_applied: str = ""


class ViralHookSkill(Skill):
    name = "viral_hook"
    description = "Gera ganchos virais para abertura de conteúdo, com suporte a contexto de nicho."

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

        # Aplicar direção do gancho do NicheContext se disponível
        hook_direction = input.hook_direction or self._infer_direction(input.posicao)

        best_template = HOOK_TEMPLATES.get(input.hook_type, HOOK_TEMPLATES["provocacao"])
        try:
            best_hook = best_template.format(
                topic=input.topic,
                audience=input.audience,
                pct=97,
            )
        except KeyError:
            best_hook = hooks[0]

        # Aplicar ângulo do nicho ao melhor gancho se disponível
        if input.angulo and input.angulo not in best_hook:
            best_hook = f"{best_hook} ({input.angulo})"

        return ViralHookOutput(
            hooks=hooks,
            best_hook=best_hook,
            hook_type_used=input.hook_type,
            hook_direction_applied=hook_direction,
        )

    def _infer_direction(self, posicao: str) -> str:
        directions = {
            "provocacao":   "Começa com a afirmação que desafia — não com a pergunta",
            "educacao":     "Começa com o que a pessoa não sabe que não sabe",
            "opiniao":      "Começa com a posição — não com a contextualização",
            "demonstracao": "Começa com o resultado — não com o processo",
        }
        return directions.get(posicao, "")

    def input_schema(self) -> dict:
        return ViralHookInput.model_json_schema()
