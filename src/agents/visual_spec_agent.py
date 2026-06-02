"""
VisualSpecAgent

Recebe NicheContext + ClientContext + ContentSpec
Gera especificação visual completa por slide.

Não gera imagem. Gera a instrução precisa
para o HTMLRenderer produzir o visual correto.
"""

import re
from src.core.agent import Agent, AgentContext, AgentResult
from src.core.models import (
    ClientContext,
    EditorialPosition,
    NicheContext,
    SlideRole,
    SlideSpec,
    VisualSpec,
    VisualStyle,
    VisualType,
)

# Mapeamento posição editorial → estilo visual
POSITION_TO_STYLE: dict[EditorialPosition, VisualStyle] = {
    EditorialPosition.PROVOCACAO:   VisualStyle.BOLD,
    EditorialPosition.EDUCACAO:     VisualStyle.CLEAN,
    EditorialPosition.OPINIAO:      VisualStyle.EDITORIAL,
    EditorialPosition.DEMONSTRACAO: VisualStyle.TECHNICAL,
}

# Mapeamento posição editorial → tipo visual
POSITION_TO_VISUAL_TYPE: dict[EditorialPosition, VisualType] = {
    EditorialPosition.PROVOCACAO:   VisualType.TIPOGRAFICO,
    EditorialPosition.EDUCACAO:     VisualType.HIBRIDO,
    EditorialPosition.OPINIAO:      VisualType.FOTO_TEXTO,
    EditorialPosition.DEMONSTRACAO: VisualType.SCREENSHOT,
}

# Mapeamento nicho slug → estilo visual padrão
NICHO_STYLE_HINTS: dict[str, VisualStyle] = {
    "inteligencia-artificial": VisualStyle.TECHNICAL,
    "saude-estetica":          VisualStyle.CLEAN,
    "juridico":                VisualStyle.EDITORIAL,
    "seguros":                 VisualStyle.CLEAN,
    "construcao":              VisualStyle.BOLD,
    "moda":                    VisualStyle.EDITORIAL,
}

LAYOUT_MATRIX: dict[tuple, str] = {
    (SlideRole.GANCHO,   VisualStyle.BOLD):      "center",
    (SlideRole.GANCHO,   VisualStyle.EDITORIAL):  "overlay",
    (SlideRole.GANCHO,   VisualStyle.TECHNICAL):  "left",
    (SlideRole.GANCHO,   VisualStyle.CLEAN):      "center",
    (SlideRole.CONTEUDO, VisualStyle.BOLD):       "left",
    (SlideRole.CONTEUDO, VisualStyle.CLEAN):      "left",
    (SlideRole.CONTEUDO, VisualStyle.TECHNICAL):  "left",
    (SlideRole.PROVA,    VisualStyle.TECHNICAL):  "center",
    (SlideRole.PROVA,    VisualStyle.CLEAN):      "center",
    (SlideRole.CTA,      VisualStyle.BOLD):       "center",
    (SlideRole.CTA,      VisualStyle.CLEAN):      "center",
}


class VisualSpecAgent(Agent):
    name = "VisualSpecAgent"
    role = "Diretor de arte e estrategista visual"
    goal = (
        "Gerar especificação visual precisa por slide, "
        "alinhada à identidade do cliente e ao contexto de nicho."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        client_ctx = context.metadata.get("client_context")
        niche_data = context.metadata.get("NicheIntelligenceAgent", {})
        copies = context.metadata.get("CopyAgent", {}).get("copies", [])

        if client_ctx is None or not copies:
            return AgentResult(
                agent=self.name,
                success=False,
                output={},
                error="client_context ou copies ausentes no metadata.",
            )

        niche_context: NicheContext | None = niche_data.get("_niche_context")
        if niche_context is None:
            return AgentResult(
                agent=self.name,
                success=False,
                output={},
                error="NicheContext não encontrado — rode NicheIntelligenceAgent primeiro.",
            )

        spec = await self.generate(
            client=client_ctx,
            niche_context=niche_context,
            copies=copies,
            platform=context.platform or "instagram",
            format=context.metadata.get("format", "1:1"),
        )

        return AgentResult(
            agent=self.name,
            success=True,
            output={"visual_spec": spec},
        )

    async def generate(
        self,
        client: ClientContext,
        niche_context: NicheContext,
        copies: list[dict],
        platform: str = "instagram",
        format: str = "1:1",
    ) -> VisualSpec:
        style = self._determine_style(client, niche_context)
        visual_type = POSITION_TO_VISUAL_TYPE.get(niche_context.posicao, VisualType.HIBRIDO)
        mood = await self._determine_mood(client, niche_context)
        slides = await self._generate_slides(copies, client, niche_context, style, visual_type)
        global_css = self._generate_global_css(client, style)

        return VisualSpec(
            client=client,
            niche_context=niche_context,
            style=style,
            visual_type=visual_type,
            mood=mood,
            format=format,
            slides=slides,
            global_css=global_css,
        )

    # ── style / mood ──────────────────────────────────────────────────────────

    def _determine_style(self, client: ClientContext, niche_ctx: NicheContext) -> VisualStyle:
        if client.style != VisualStyle.CLEAN:
            return client.style
        # Try nicho slug hint
        nicho_slug = self._slugify(client.nicho)
        hint = NICHO_STYLE_HINTS.get(nicho_slug)
        if hint:
            return hint
        # Partial match (e.g. "seguros-de-vida" matches "seguros")
        for key, style in NICHO_STYLE_HINTS.items():
            if key in nicho_slug:
                return style
        return POSITION_TO_STYLE.get(niche_ctx.posicao, VisualStyle.CLEAN)

    async def _determine_mood(self, client: ClientContext, niche_ctx: NicheContext) -> str:
        prompt = (
            f"Cliente: {client.name} — nicho: {client.nicho}\n"
            f"Ângulo do conteúdo: {niche_ctx.angulo}\n"
            f"Posição editorial: {niche_ctx.posicao.value}\n"
            f"Tom do nicho: {niche_ctx.linguagem.tom}\n\n"
            "Defina o mood visual em uma palavra ou frase curta.\n"
            "Exemplos: 'urgente e direto', 'premium e calmo', "
            "'técnico e confiável', 'humano e próximo', 'ousado e disruptivo'\n\n"
            "Retorne apenas o mood."
        )
        return await self._provider.generate(
            system="Defina mood visual. Resposta curta.",
            user=prompt,
            temperature=0.3,
        )

    # ── slides ────────────────────────────────────────────────────────────────

    async def _generate_slides(
        self,
        copies: list[dict],
        client: ClientContext,
        niche_ctx: NicheContext,
        style: VisualStyle,
        visual_type: VisualType,
    ) -> list[SlideSpec]:
        slides = []
        total = len(copies)

        for i, copy in enumerate(copies):
            role = self._determine_role(i, total, copy)
            layout = self._determine_layout(role, style)
            emphasis = await self._find_emphasis_words(copy.get("headline", copy.get("hook", "")))

            slides.append(SlideSpec(
                role=role,
                slide_number=i + 1,
                total_slides=total,
                headline=copy.get("headline", copy.get("hook", "")),
                body=copy.get("body"),
                visual_type=self._slide_visual_type(role, visual_type),
                layout=layout,
                focal_point=self._focal_point(role, layout),
                emphasis=emphasis,
                cta=copy.get("cta") if role == SlideRole.CTA else None,
                background_treatment=self._bg_treatment(role, style),
            ))

        return slides

    def _determine_role(self, index: int, total: int, copy: dict) -> SlideRole:
        if index == 0:
            return SlideRole.GANCHO
        if index == total - 1:
            return SlideRole.CTA
        if copy.get("has_data"):
            return SlideRole.PROVA
        return SlideRole.CONTEUDO

    def _determine_layout(self, role: SlideRole, style: VisualStyle) -> str:
        return LAYOUT_MATRIX.get((role, style), "left")

    def _slide_visual_type(self, role: SlideRole, base_type: VisualType) -> VisualType:
        overrides = {
            SlideRole.GANCHO:   base_type,
            SlideRole.CONTEUDO: VisualType.TIPOGRAFICO,
            SlideRole.PROVA:    VisualType.DADOS,
            SlideRole.CTA:      VisualType.TIPOGRAFICO,
        }
        return overrides.get(role, base_type)

    def _focal_point(self, role: SlideRole, layout: str) -> str:
        if role == SlideRole.GANCHO:
            return "headline — máximo peso visual"
        if role == SlideRole.CTA:
            return "chamada para ação — destaque pela cor"
        if layout == "center":
            return "centro — hierarquia clara"
        return "linha superior — leitura natural"

    def _bg_treatment(self, role: SlideRole, style: VisualStyle) -> str:
        if style == VisualStyle.DARK:
            return "solid-dark-grain"
        if style == VisualStyle.EDITORIAL:
            return "image-overlay" if role == SlideRole.GANCHO else "solid-light"
        if style == VisualStyle.TECHNICAL:
            return "dark-grid"
        return "solid-light"

    async def _find_emphasis_words(self, headline: str) -> list[str]:
        if not headline:
            return []
        prompt = (
            f'Headline: "{headline}"\n'
            "Identifique 1-3 palavras que merecem destaque visual.\n"
            "Critério: palavras que carregam o peso emocional ou o dado mais importante.\n"
            "Retorne apenas as palavras separadas por vírgula."
        )
        result = await self._provider.generate(
            system="Identifique palavras de destaque.",
            user=prompt,
            temperature=0.1,
        )
        return [w.strip() for w in result.split(",") if w.strip()][:3]

    # ── CSS ───────────────────────────────────────────────────────────────────

    def _generate_global_css(self, client: ClientContext, style: VisualStyle) -> str:
        p = client.palette
        t = client.typography

        base = (
            f":root {{\n"
            f"  --primary:    {p.primary};\n"
            f"  --secondary:  {p.secondary};\n"
            f"  --accent:     {p.accent};\n"
            f"  --bg:         {p.background};\n"
            f"  --text:       {p.text};\n"
            f"  --text-light: {p.text_light};\n"
            f"  --font-h:     '{t.heading}', serif;\n"
            f"  --font-b:     '{t.body}', sans-serif;\n"
            f"  --font-m:     '{t.mono}', monospace;\n"
            f"}}\n"
        )

        style_overrides = {
            VisualStyle.DARK: (
                ":root {\n"
                "  --slide-bg:      #0a0a0a;\n"
                "  --slide-text:    #fafafa;\n"
                "  --slide-accent:  var(--accent);\n"
                "  --grain-opacity: 0.04;\n"
                "}\n"
            ),
            VisualStyle.CLEAN: (
                ":root {\n"
                "  --slide-bg:      #ffffff;\n"
                "  --slide-text:    var(--text);\n"
                "  --slide-accent:  var(--primary);\n"
                "  --grain-opacity: 0;\n"
                "}\n"
            ),
            VisualStyle.BOLD: (
                ":root {\n"
                "  --slide-bg:      var(--primary);\n"
                "  --slide-text:    #ffffff;\n"
                "  --slide-accent:  var(--accent);\n"
                "  --grain-opacity: 0.03;\n"
                "}\n"
            ),
            VisualStyle.TECHNICAL: (
                ":root {\n"
                "  --slide-bg:      #0d0d0d;\n"
                "  --slide-text:    #e8e8e8;\n"
                "  --slide-accent:  var(--accent);\n"
                "  --grain-opacity: 0.05;\n"
                "  --grid-color:    rgba(255,255,255,0.04);\n"
                "}\n"
            ),
            VisualStyle.EDITORIAL: (
                ":root {\n"
                "  --slide-bg:      var(--bg);\n"
                "  --slide-text:    var(--text);\n"
                "  --slide-accent:  var(--primary);\n"
                "  --grain-opacity: 0.02;\n"
                "}\n"
            ),
            VisualStyle.WARM: (
                ":root {\n"
                "  --slide-bg:      #fdf6ec;\n"
                "  --slide-text:    var(--text);\n"
                "  --slide-accent:  var(--accent);\n"
                "  --grain-opacity: 0.02;\n"
                "}\n"
            ),
        }
        return base + style_overrides.get(style, "")

    @staticmethod
    def _slugify(text: str) -> str:
        slug = text.lower().strip()
        for src, dst in [
            ("[áàãâä]", "a"), ("[éèêë]", "e"), ("[íìîï]", "i"),
            ("[óòõôö]", "o"), ("[úùûü]", "u"), ("[ç]", "c"),
        ]:
            slug = re.sub(src, dst, slug)
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")
