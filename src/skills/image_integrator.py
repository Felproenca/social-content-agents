"""
ImageIntegrator

Após o operador fazer upload da imagem,
incorpora no HTML do slide como background com overlay.
"""

import shutil
from pathlib import Path

from src.core.models import PipelineStatus, SlideProcessingMode

# Marcador inserido pelo HTMLRenderer nos slides que aguardam imagem
IMAGE_PLACEHOLDER = "/* IMAGE_PLACEHOLDER */"

IMAGE_CSS = """/* IMAGEM INJETADA */
body {{
  background-image: url('{name}');
  background-size: cover;
  background-position: center;
}}
body::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,0.10) 0%,
    rgba(0,0,0,0.60) 60%,
    rgba(0,0,0,0.85) 100%
  );
  z-index: 0;
}}
"""


class ImageIntegrator:

    async def integrate(
        self,
        status: PipelineStatus,
        slide_number: int,
        image_path: str,
        html_dir: Path,
    ) -> PipelineStatus:
        """
        Copia a imagem para o diretório do conteúdo,
        injeta como background no HTML correspondente
        e atualiza o PipelineStatus.
        """
        img_dest = html_dir / f"image-slide-{slide_number:02d}.jpg"
        shutil.copy(image_path, img_dest)

        html_path = html_dir / f"slide-{slide_number:02d}.html"
        if html_path.exists():
            html = html_path.read_text(encoding="utf-8")
            html = self._inject_image(html, img_dest.name)
            html_path.write_text(html, encoding="utf-8")

        for prompt in status.image_prompts:
            if prompt.slide_number == slide_number:
                prompt.status = SlideProcessingMode.IMAGE_READY
                prompt.image_path = str(img_dest)
                break

        status.ready_to_render = all(
            p.status == SlideProcessingMode.IMAGE_READY
            for p in status.image_prompts
        )
        return status

    def _inject_image(self, html: str, image_name: str) -> str:
        css = IMAGE_CSS.format(name=image_name)
        # Substituir o placeholder se existir; caso contrário inserir antes de </style>
        if IMAGE_PLACEHOLDER in html:
            return html.replace(IMAGE_PLACEHOLDER, css, 1)
        return html.replace("</style>", f"{css}</style>", 1)
