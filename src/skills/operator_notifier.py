"""
OperatorNotifier

Quando o pipeline (excepcionalmente) precisa de imagem externa,
notifica o operador com o prompt formatado e instrução clara de upload.
"""

from src.core.models import ImagePrompt, PipelineStatus


class OperatorNotifier:

    def format_notification(self, status: PipelineStatus) -> str:
        if status.ready_to_render:
            return "Pipeline completo. Nenhuma imagem necessária."

        sep = "=" * 60
        lines = [
            f"\n{sep}",
            "PIPELINE PAUSADO — IMAGEM NECESSÁRIA",
            sep,
            f"Cliente:               {status.client_slug}",
            f"Conteúdo:              {status.content_id}",
            f"Slides automáticos:    {status.html_only}",
            f"Aguardando imagem:     {status.needs_image}",
            sep,
        ]

        for prompt in status.image_prompts:
            lines += self._format_prompt(prompt)

        lines += [
            f"\n{sep}",
            "APÓS GERAR A IMAGEM:",
            "  python -m src.main upload-image \\",
            f"    --content {status.content_id} \\",
            "    --slide [NÚMERO] \\",
            "    --file [CAMINHO_DA_IMAGEM]",
            f"{sep}\n",
        ]

        return "\n".join(lines)

    def _format_prompt(self, p: ImagePrompt) -> list[str]:
        lines = [
            f"\nSLIDE {p.slide_number}",
            "-" * 40,
            "\nPROMPT (cole no serviço externo):",
            p.prompt_en,
            "\nNEGATIVO (o que evitar):",
            p.negative,
            "\nNOTAS PARA VOCÊ:",
            p.style_notes,
            "\nDICAS POR SERVIÇO:",
        ]

        h = p.service_hints
        if h.get("midjourney"):
            lines.append(f"  Midjourney: adicione ao final → {h['midjourney']}")
        if h.get("ideogram"):
            lines.append(f"  Ideogram:   {h['ideogram']}")
        if h.get("pollinations"):
            lines.append(f"  Pollinations: {h['pollinations']}")
        if h.get("dalle3"):
            lines.append(f"  DALL-E 3:   {h['dalle3']}")

        lines.append(f"\nPROPORÇÃO: {p.aspect_ratio}\n")
        return lines
