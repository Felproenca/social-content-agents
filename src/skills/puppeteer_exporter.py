"""
PuppeteerExporter

Converte HTMLs gerados pelo HTMLRenderer em PNGs prontos para publicação.
Requer: pip install pyppeteer  (extras: pip install -e ".[visual]")
"""

import asyncio
from pathlib import Path


class PuppeteerExporter:

    def __init__(self, width: int = 1080, height: int = 1080):
        self.width = width
        self.height = height

    async def export(
        self,
        html_paths: list[Path],
        output_dir: Path,
    ) -> list[Path]:
        """
        Converte lista de HTMLs em PNGs 2x (deviceScaleFactor=2).
        Retorna lista de paths dos PNGs gerados.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            from pyppeteer import launch
        except ImportError:
            raise ImportError(
                "pyppeteer não instalado. Execute: pip install pyppeteer\n"
                "ou: pip install -e '[.visual]'"
            )

        browser = await launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                f"--window-size={self.width},{self.height}",
            ],
        )

        png_paths: list[Path] = []

        try:
            for html_path in html_paths:
                png_path = output_dir / html_path.name.replace(".html", ".png")
                page = await browser.newPage()
                await page.setViewport({
                    "width":            self.width,
                    "height":           self.height,
                    "deviceScaleFactor": 2,   # 2x → PNG 2160×2160
                })
                await page.goto(
                    f"file://{html_path.absolute()}",
                    waitUntil="networkidle0",
                )
                await page.waitForFunction("document.fonts.ready")
                await page.screenshot({
                    "path": str(png_path),
                    "type": "png",
                    "fullPage": False,
                    "clip": {
                        "x": 0, "y": 0,
                        "width": self.width,
                        "height": self.height,
                    },
                })
                await page.close()
                png_paths.append(png_path)
        finally:
            await browser.close()

        return png_paths
