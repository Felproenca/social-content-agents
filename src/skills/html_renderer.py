"""
HTMLRenderer

Recebe VisualSpec e gera HTML completo por slide.
Cada slide é um arquivo HTML standalone
que o Puppeteer converte em PNG.

Sem dependências externas de design.
O sistema controla tipografia, cores,
hierarquia e composição com precisão.
"""

import re
from pathlib import Path
from typing import Any

from src.core.models import SlideRole, SlideSpec, VisualSpec, VisualStyle, VisualType

# ── Dimensões por formato ─────────────────────────────────────────────────────
FORMATS: dict[str, tuple[int, int]] = {
    "1:1":  (1080, 1080),
    "4:5":  (1080, 1350),
    "9:16": (1080, 1920),
}

# ── Parâmetros tipográficos por SlideRole ─────────────────────────────────────
TYPO: dict[SlideRole, dict[str, Any]] = {
    SlideRole.GANCHO: {
        "headline_size": 72, "headline_weight": 700,
        "headline_lh": 1.05, "headline_ls": -0.03,
        "headline_maxw": 90, "body_size": 18,
        "body_maxw": 80, "body_mt": 24,
        "cta_size": 36, "data_size": 96,
    },
    SlideRole.CONTEUDO: {
        "headline_size": 48, "headline_weight": 600,
        "headline_lh": 1.15, "headline_ls": -0.02,
        "headline_maxw": 90, "body_size": 17,
        "body_maxw": 85, "body_mt": 20,
        "cta_size": 32, "data_size": 80,
    },
    SlideRole.PROVA: {
        "headline_size": 36, "headline_weight": 500,
        "headline_lh": 1.2, "headline_ls": -0.01,
        "headline_maxw": 80, "body_size": 16,
        "body_maxw": 80, "body_mt": 16,
        "cta_size": 28, "data_size": 120,
    },
    SlideRole.CTA: {
        "headline_size": 48, "headline_weight": 600,
        "headline_lh": 1.1, "headline_ls": -0.02,
        "headline_maxw": 85, "body_size": 16,
        "body_maxw": 80, "body_mt": 20,
        "cta_size": 42, "data_size": 80,
    },
}

GRAIN_OPACITY: dict[VisualStyle, float] = {
    VisualStyle.DARK:      0.05,
    VisualStyle.TECHNICAL: 0.06,
    VisualStyle.BOLD:      0.03,
    VisualStyle.EDITORIAL: 0.02,
    VisualStyle.CLEAN:     0.00,
    VisualStyle.WARM:      0.02,
}

LAYOUT_JUSTIFY: dict[str, tuple[str, str]] = {
    "center":  ("center", "center"),
    "left":    ("flex-end", "flex-start"),
    "overlay": ("flex-end", "flex-start"),
    "split":   ("space-between", "flex-start"),
}

STYLE_CUSTOM_CSS: dict[VisualStyle, str] = {
    VisualStyle.EDITORIAL: ".headline { font-style: italic; font-weight: 500; }\n",
    VisualStyle.BOLD: (
        ".headline { text-transform: uppercase; letter-spacing: -0.04em; }\n"
        ".accent-line { width: 60px; height: 3px; }\n"
    ),
}


class HTMLRenderer:

    FORMATS = FORMATS

    async def render(self, spec: VisualSpec, output_dir: Path) -> list[Path]:
        """Gera um HTML por slide. Retorna lista de paths para o PuppeteerExporter."""
        output_dir.mkdir(parents=True, exist_ok=True)
        html_paths = []

        for slide in spec.slides:
            html = self._build_slide_html(slide, spec)
            path = output_dir / f"slide-{slide.slide_number:02d}.html"
            path.write_text(html, encoding="utf-8")
            html_paths.append(path)

        return html_paths

    def _build_slide_html(self, slide: SlideSpec, spec: VisualSpec) -> str:
        w, h = FORMATS.get(spec.format, (1080, 1080))
        t = spec.client.typography
        style = spec.style
        typo = TYPO.get(slide.role, TYPO[SlideRole.CONTEUDO])

        justify, align = LAYOUT_JUSTIFY.get(slide.layout, ("flex-end", "flex-start"))
        padding = "64px" if spec.format == "1:1" else "72px 64px"
        mark_side = "left" if slide.layout == "left" else "right"
        grain = GRAIN_OPACITY.get(style, 0.02)

        body_html = self._build_body(slide, spec)
        grid_css = self._grid_overlay(style)
        custom_css = STYLE_CUSTOM_CSS.get(style, "")

        # Build HTML without .format() to avoid CSS brace conflicts
        # Use explicit string assembly instead
        font_h = t.heading.replace(" ", "+")
        font_b = t.body.replace(" ", "+")

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family={font_h}:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,500&family={font_b}:wght@300;400;500;600;700;800&family=Syne+Mono&display=swap" rel="stylesheet">
<style>
{spec.global_css}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{
  width: {w}px;
  height: {h}px;
  overflow: hidden;
}}

body {{
  background: var(--slide-bg);
  color: var(--slide-text);
  font-family: var(--font-b);
  position: relative;
}}

body::before {{
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='{grain}'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
}}

{grid_css}

.slide {{
  width: 100%;
  height: 100%;
  padding: {padding};
  display: flex;
  flex-direction: column;
  justify-content: {justify};
  align-items: {align};
  position: relative;
  z-index: 1;
}}

.client-mark {{
  position: absolute;
  top: 28px;
  {mark_side}: 32px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.7;
}}
.client-mark-name {{
  font-family: var(--font-b);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--slide-text);
  opacity: 0.6;
}}

.slide-counter {{
  position: absolute;
  top: 28px;
  right: 32px;
  font-family: var(--font-m);
  font-size: 11px;
  color: var(--slide-text);
  opacity: 0.3;
  letter-spacing: 0.1em;
}}

.accent-line {{
  width: 40px;
  height: 2px;
  background: var(--slide-accent);
  margin-bottom: 20px;
}}

.headline {{
  font-family: var(--font-h);
  font-size: {typo["headline_size"]}px;
  font-weight: {typo["headline_weight"]};
  line-height: {typo["headline_lh"]};
  letter-spacing: {typo["headline_ls"]}em;
  color: var(--slide-text);
  max-width: {typo["headline_maxw"]}%;
  position: relative;
  z-index: 2;
}}

.emphasis {{
  color: var(--slide-accent);
  font-style: italic;
}}

.body-text {{
  font-family: var(--font-b);
  font-size: {typo["body_size"]}px;
  line-height: 1.7;
  color: var(--slide-text);
  opacity: 0.75;
  max-width: {typo["body_maxw"]}%;
  margin-top: {typo["body_mt"]}px;
  font-weight: 400;
}}

.cta-text {{
  font-family: var(--font-h);
  font-size: {typo["cta_size"]}px;
  font-weight: 600;
  color: var(--slide-text);
  margin-bottom: 20px;
  line-height: 1.2;
}}
.cta-action {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: var(--slide-accent);
  color: var(--slide-bg);
  padding: 14px 28px;
  border-radius: 6px;
  font-family: var(--font-b);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.data-number {{
  font-family: var(--font-h);
  font-size: {typo["data_size"]}px;
  font-weight: 500;
  line-height: 1;
  color: var(--slide-accent);
  margin-bottom: 12px;
}}
.data-label {{
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--slide-text);
  opacity: 0.5;
  font-weight: 600;
}}

.divider {{
  width: 100%;
  height: 0.5px;
  background: var(--slide-text);
  opacity: 0.1;
  margin: 20px 0;
}}

.mos-badge {{
  position: absolute;
  bottom: 28px;
  right: 32px;
  display: flex;
  align-items: baseline;
  gap: 2px;
  opacity: 0.25;
}}
.mos-m {{
  font-family: var(--font-b);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--slide-text);
}}
.mos-slash {{
  font-family: var(--font-b);
  font-size: 10px;
  font-weight: 200;
  color: var(--slide-text);
}}
.mos-os {{
  font-family: var(--font-h);
  font-size: 10px;
  font-style: italic;
  color: var(--slide-accent);
}}

{custom_css}
</style>
</head>
<body>
{body_html}
</body>
</html>"""

    # ── body builders ─────────────────────────────────────────────────────────

    def _build_body(self, slide: SlideSpec, spec: VisualSpec) -> str:
        client = spec.client
        headline = self._apply_emphasis(slide.headline, slide.emphasis)

        mark = (
            f'<div class="client-mark">'
            f'<span class="client-mark-name">@{client.slug}</span>'
            f'</div>'
        )
        counter = (
            f'<div class="slide-counter">{slide.slide_number}/{slide.total_slides}</div>'
            if slide.total_slides > 1 else ""
        )
        badge = (
            '<div class="mos-badge">'
            '<span class="mos-m">Marketing</span>'
            '<span class="mos-slash">/</span>'
            '<span class="mos-os">OS</span>'
            '</div>'
        )

        if slide.role == SlideRole.GANCHO:
            content = self._gancho_content(headline, slide)
        elif slide.role == SlideRole.PROVA:
            content = self._prova_content(headline, slide)
        elif slide.role == SlideRole.CTA:
            content = self._cta_content(slide)
        else:
            content = self._conteudo_content(headline, slide)

        return (
            f"{mark}\n{counter}\n"
            f'<div class="slide">\n{content}\n</div>\n'
            f"{badge}"
        )

    def _gancho_content(self, headline: str, slide: SlideSpec) -> str:
        line = '<div class="accent-line"></div>' if slide.layout != "center" else ""
        body = f'<p class="body-text">{slide.body}</p>' if slide.body else ""
        return f"{line}\n<h1 class=\"headline\">{headline}</h1>\n{body}"

    def _conteudo_content(self, headline: str, slide: SlideSpec) -> str:
        body = f'<p class="body-text">{slide.body}</p>' if slide.body else ""
        return f'<div class="accent-line"></div>\n<h2 class="headline">{headline}</h2>\n{body}'

    def _prova_content(self, headline: str, slide: SlideSpec) -> str:
        match = re.search(r"[\d,.]+[%xkK+]?", headline)
        if match:
            number = match.group()
            label = headline.replace(number, "").strip(" -–—:")
            body = f'<p class="body-text">{slide.body}</p>' if slide.body else ""
            return (
                f'<div class="data-number">{number}</div>\n'
                f'<div class="data-label">{label}</div>\n'
                f'<div class="divider"></div>\n{body}'
            )
        return self._conteudo_content(headline, slide)

    def _cta_content(self, slide: SlideSpec) -> str:
        action = slide.cta or "Fale com a gente"
        return (
            f'<p class="cta-text">{slide.headline}</p>\n'
            f'<div class="cta-action">{action} →</div>'
        )

    def _apply_emphasis(self, text: str, emphasis: list[str]) -> str:
        for word in emphasis:
            if word:
                text = text.replace(word, f'<em class="emphasis">{word}</em>', 1)
        return text

    def _grid_overlay(self, style: VisualStyle) -> str:
        if style != VisualStyle.TECHNICAL:
            return ""
        return (
            "body::after {\n"
            "  content: '';\n"
            "  position: absolute;\n"
            "  inset: 0;\n"
            "  background-image:\n"
            "    linear-gradient(var(--grid-color) 1px, transparent 1px),\n"
            "    linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);\n"
            "  background-size: 40px 40px;\n"
            "  pointer-events: none;\n"
            "  z-index: 0;\n"
            "}\n"
        )
