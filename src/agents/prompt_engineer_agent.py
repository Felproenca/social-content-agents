"""
PromptEngineerAgent — fluxo híbrido

Princípio: HTML resolve 95% dos casos.
Imagem externa só quando as 3 condições forem verdadeiras:
  1. SlideRole.GANCHO
  2. VisualType.FOTO_TEXTO
  3. background_treatment == "image-overlay"

Tudo o mais → HTML_ONLY, zero interrupção.
"""

import json
import re

from src.core.agent import Agent, AgentContext, AgentResult
from src.core.models import (
    ImagePrompt,
    PipelineStatus,
    SlideProcessingMode,
    SlideRole,
    SlideSpec,
    VisualSpec,
    VisualType,
)

# Tipos que nunca precisam de imagem externa
HTML_ONLY_TYPES = {VisualType.TIPOGRAFICO, VisualType.DADOS, VisualType.SCREENSHOT}

PROMPT_SYSTEM = """
Você é um diretor de fotografia e arte especializado
em conteúdo para redes sociais.

Seu trabalho é gerar prompts de imagem precisos que:
1. Capturem o mood emocional do conteúdo
2. Sejam alinhados com a identidade visual do cliente
3. Evitem o genérico de banco de imagens
4. Resultem em imagem que para o scroll

Princípios de um bom prompt de imagem:
→ Específico sobre ângulo, luz e composição
→ Define o que NÃO incluir (tão importante quanto o que incluir)
→ Menciona referência fotográfica real quando relevante
→ Alinha cores com a paleta do cliente
→ Evita poses óbvias, sorrisos forçados, stock photo energy
→ Prefere momentos genuínos, ângulos não convencionais,
  detalhes que sugerem contexto sem mostrar tudo

Retorne APENAS o JSON solicitado, sem texto adicional.
"""

PROMPT_USER = """
Gere um prompt de imagem para este slide:

CONTEXTO DO SLIDE:
  Role: {role}
  Headline: {headline}
  Mood: {mood}
  Layout: {layout}
  Background treatment: {bg_treatment}

IDENTIDADE DO CLIENTE:
  Nome: {client_name}
  Nicho: {nicho}
  Paleta principal: {primary} e {accent}
  Estilo visual: {style}
  Tom: {tom}

ÂNGULO DO CONTEÚDO:
  {angulo}

POSIÇÃO EDITORIAL:
  {posicao}

FORMATO:
  {format}

Retorne JSON com esta estrutura exata:
{{
  "prompt_en": "prompt completo em inglês, detalhado, 80-120 palavras",
  "prompt_pt": "mesmo prompt em português para referência",
  "negative": "elementos a evitar — em inglês, separados por vírgula",
  "style_notes": "notas para o operador sobre o que buscar",
  "service_hints": {{
    "midjourney": "parâmetros específicos para Midjourney",
    "ideogram": "configurações para Ideogram",
    "pollinations": "ajustes para Pollinations",
    "dalle3": "instrução adicional para DALL-E 3"
  }}
}}
"""


class PromptEngineerAgent(Agent):
    name = "PromptEngineerAgent"
    role = "Diretor de fotografia e arte para conteúdo social"
    goal = (
        "Identificar os raros slides que genuinamente precisam de foto real "
        "e gerar o prompt mais preciso possível para o operador."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        visual_spec = context.metadata.get("visual_spec")
        content_id = context.metadata.get("content_id", "")

        if visual_spec is None:
            return AgentResult(
                agent=self.name, success=False, output={},
                error="visual_spec ausente — rode VisualSpecAgent primeiro.",
            )

        status = await self.analyze(visual_spec, content_id)
        return AgentResult(
            agent=self.name,
            success=True,
            output={"pipeline_status": status},
        )

    async def analyze(self, visual_spec: VisualSpec, content_id: str) -> PipelineStatus:
        """
        Analisa todos os slides.
        Só gera prompt quando _needs_external_image() retorna True.
        """
        html_only: list[int] = []
        needs_image: list[int] = []
        image_prompts: list[ImagePrompt] = []

        for slide in visual_spec.slides:
            if self._needs_external_image(slide):
                needs_image.append(slide.slide_number)
                prompt = await self._generate_prompt(slide, visual_spec)
                image_prompts.append(prompt)
            else:
                html_only.append(slide.slide_number)

        return PipelineStatus(
            client_slug=visual_spec.client.slug,
            content_id=content_id,
            total_slides=len(visual_spec.slides),
            html_only=html_only,
            needs_image=needs_image,
            image_prompts=image_prompts,
            ready_to_render=len(needs_image) == 0,
        )

    @staticmethod
    def _needs_external_image(slide: SlideSpec) -> bool:
        """
        Imagem externa só quando as 3 condições forem verdadeiras.
        Em todos os outros casos: HTML resolve.
        """
        if slide.visual_type in HTML_ONLY_TYPES:
            return False
        if slide.role == SlideRole.CTA:
            return False
        if slide.role == SlideRole.CONTEUDO:
            return False
        # Única exceção: gancho editorial explicitamente pedindo foto real
        return (
            slide.role == SlideRole.GANCHO
            and slide.visual_type == VisualType.FOTO_TEXTO
            and slide.background_treatment == "image-overlay"
        )

    async def _generate_prompt(self, slide: SlideSpec, spec: VisualSpec) -> ImagePrompt:
        p = spec.client.palette
        niche_ctx = spec.niche_context

        user_msg = PROMPT_USER.format(
            role=slide.role.value,
            headline=slide.headline,
            mood=spec.mood,
            layout=slide.layout,
            bg_treatment=slide.background_treatment,
            client_name=spec.client.name,
            nicho=spec.client.nicho,
            primary=p.primary,
            accent=p.accent,
            style=spec.style.value,
            tom=niche_ctx.linguagem.tom,
            angulo=niche_ctx.angulo,
            posicao=niche_ctx.posicao.value,
            format=spec.format,
        )

        response = await self._provider.generate(
            system=PROMPT_SYSTEM,
            user=user_msg,
            temperature=0.4,
        )

        match = re.search(r"\{.*\}", response, re.DOTALL)
        data: dict = json.loads(match.group()) if match else {}

        return ImagePrompt(
            slide_number=slide.slide_number,
            prompt_en=data.get("prompt_en", ""),
            prompt_pt=data.get("prompt_pt", ""),
            negative=data.get("negative", ""),
            style_notes=data.get("style_notes", ""),
            aspect_ratio=spec.format,
            service_hints=data.get("service_hints", {}),
            status=SlideProcessingMode.NEEDS_IMAGE,
        )
