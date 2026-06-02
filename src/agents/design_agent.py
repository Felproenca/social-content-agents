import json
from src.core.agent import Agent, AgentContext, AgentResult


class DesignAgent(Agent):
    name = "DesignAgent"
    role = "Diretor de arte e engenheiro de prompts visuais"
    goal = (
        "Criar prompts detalhados para geração de imagens (Midjourney, DALL-E, Flux) "
        "que complementem o conteúdo textual e ampliem o engajamento."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        copies = context.metadata.get("CopyAgent", {}).get("copies", [])
        trends = context.metadata.get("TrendAgent", {})

        messages = [
            {
                "role": "user",
                "content": (
                    f"Tópico: '{context.topic}'\n"
                    f"Plataforma: {context.platform or 'geral'}\n"
                    f"Tom visual: {context.tone}\n"
                    f"Copies criadas: {json.dumps(copies[:2], ensure_ascii=False)}\n"
                    f"Tendências visuais: {json.dumps(trends.get('viral_patterns', []), ensure_ascii=False)}\n\n"
                    "Crie prompts visuais para cada copy. Retorne JSON com lista 'visuals', cada item com:\n"
                    "- prompt_en: prompt em inglês para Midjourney/DALL-E/Flux\n"
                    "- prompt_style: estilo visual (ex: 'photorealistic', 'flat design', '3D render')\n"
                    "- color_palette: paleta de cores sugerida\n"
                    "- dimensions: dimensões ideais por plataforma\n"
                    "- mood: sensação/emoção que a imagem deve transmitir\n"
                    "- negative_prompt: o que evitar na imagem"
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
