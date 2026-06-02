from pydantic import Field
from src.core.skill import Skill, SkillInput, SkillOutput


class CopywritingInput(SkillInput):
    topic: str
    platform: str = "linkedin"
    tone: str = "professional"
    audience: str = ""
    objective: str = "engagement"
    length: str = "medium"


class CopywritingOutput(SkillOutput):
    copy: str = ""
    hook: str = ""
    cta: str = ""
    word_count: int = 0


class CopywritingSkill(Skill):
    name = "copywriting"
    description = "Escreve copy persuasivo adaptado à plataforma, tom e objetivo."

    async def run(self, input: CopywritingInput) -> CopywritingOutput:  # type: ignore[override]
        # This skill is meant to be called by an agent that provides the LLM.
        # Standalone usage returns a placeholder — embed inside CopyAgent for full output.
        return CopywritingOutput(
            copy=f"[Copywriting skill — integrar com CopyAgent para output real]",
            hook="",
            cta="",
            word_count=0,
        )

    def input_schema(self) -> dict:
        return CopywritingInput.model_json_schema()
