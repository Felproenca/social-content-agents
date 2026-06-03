"""
Social Content Agents — entrypoint principal.
Roda como API FastAPI ou como CLI.
"""

import argparse
import asyncio
import json
import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.config import settings
from src.storage.db import init_db
from src.workflows.content_factory import ContentFactory
from src.workflows.campaign_builder import CampaignBuilder

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Social Content Agents",
    description="Framework de deep agents para criação de conteúdo em escala",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Social Content Agents iniciado.")


# ── Request models ─────────────────────────────────────────────────────────────

class ContentRequest(BaseModel):
    topic: str
    platform: str = "linkedin"
    tone: str = "thought_leader"
    audience: str = ""
    variations: int = 3
    auto_publish: bool = False


class CampaignRequest(BaseModel):
    name: str
    topic: str
    platforms: list[str] = ["linkedin", "instagram"]
    tone: str = "thought_leader"
    audience: str = ""
    variations_per_platform: int = 2


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/content/generate")
async def generate_content(req: ContentRequest):
    factory = ContentFactory()
    result = await factory.run(
        topic=req.topic,
        platform=req.platform,
        tone=req.tone,
        audience=req.audience,
        variations=req.variations,
        auto_publish=req.auto_publish,
    )
    return {
        "topic": result.topic,
        "platform": result.platform,
        "status": result.status,
        "copies": result.copies,
        "performance": result.performance,
        "publish_status": result.publish_status,
    }


@app.post("/campaign/build")
async def build_campaign(req: CampaignRequest):
    builder = CampaignBuilder()
    campaign = await builder.build(
        name=req.name,
        topic=req.topic,
        platforms=req.platforms,
        tone=req.tone,
        audience=req.audience,
        variations_per_platform=req.variations_per_platform,
    )
    return {
        "name": campaign.name,
        "topic": campaign.topic,
        "platforms": campaign.platforms,
        "total_copies": campaign.total_copies,
        "results": {
            p: {"copies": r.copies}
            for p, r in campaign.results.items()
        },
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

async def _cmd_generate(args: argparse.Namespace) -> None:
    await init_db()
    factory = ContentFactory()

    if args.brief:
        brief_path = args.brief
        brief = json.loads(open(brief_path, encoding="utf-8").read())
        result = await factory.run_from_brief(brief)
    else:
        result = await factory.run(
            topic=args.topic,
            platform=args.platform,
            variations=args.variations,
        )

    print("\n" + "=" * 60)
    print(f"Tópico:    {result.topic}")
    print(f"Status:    {result.status}")
    print(f"Content ID: {result.content_id or '—'}")
    print(f"Copies:    {len(result.copies)}")
    if result.html_paths:
        print(f"HTML:      {len(result.html_paths)} slides → {result.html_paths[0].parent}")
    if result.png_paths:
        print(f"PNG:       {len(result.png_paths)} exportados")
    print("=" * 60)
    print(json.dumps(result.copies, ensure_ascii=False, indent=2))


async def _cmd_upload_image(args: argparse.Namespace) -> None:
    from pathlib import Path
    from src.skills.image_integrator import ImageIntegrator

    await init_db()
    factory = ContentFactory()

    client_slug = args.content.split("-")[0] if "-" in args.content else "cliente"
    pipeline_status = await factory.load_pipeline_status(args.content, client_slug)

    if pipeline_status is None:
        print(f"Erro: status não encontrado para content_id={args.content}")
        sys.exit(1)

    html_dir = Path(f"tmp/{client_slug}/slides")
    integrator = ImageIntegrator()
    pipeline_status = await integrator.integrate(
        status=pipeline_status,
        slide_number=args.slide,
        image_path=args.file,
        html_dir=html_dir,
    )

    await factory.save_pipeline_status(pipeline_status, client_slug)

    pending = [p.slide_number for p in pipeline_status.image_prompts
               if p.status.value != "image_ready"]

    if pending:
        print(f"Imagem do slide {args.slide} registrada.")
        print(f"Aguardando slides: {pending}")
    else:
        print(f"Imagem do slide {args.slide} registrada. Todos os slides prontos!")
        print("Iniciando renderização final...")
        result = await factory.resume_after_images(args.content, client_slug)
        print(f"Renderização completa: {len(result.png_paths)} PNGs gerados.")
        if result.png_paths:
            for p in result.png_paths:
                print(f"  {p}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description="Social Content Agents CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # generate
    gen = sub.add_parser("generate", help="Gera conteúdo a partir de tópico ou brief")
    gen.add_argument("--topic", default="Inteligência Artificial no marketing")
    gen.add_argument("--platform", default="linkedin")
    gen.add_argument("--variations", type=int, default=3)
    gen.add_argument("--brief", metavar="FILE", help="Caminho para JSON de brief completo")

    # upload-image
    up = sub.add_parser("upload-image", help="Registra imagem gerada externamente para um slide")
    up.add_argument("--content", required=True, metavar="CONTENT_ID",
                    help="ID do conteúdo (ex: cliente-ai-no-marketing-20240101-120000)")
    up.add_argument("--slide", required=True, type=int, metavar="NÚMERO",
                    help="Número do slide (ex: 1)")
    up.add_argument("--file", required=True, metavar="CAMINHO",
                    help="Caminho da imagem gerada")

    # serve (default)
    sub.add_parser("serve", help="Inicia o servidor FastAPI")

    return parser


def cli():
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(_cmd_generate(args))
    elif args.command == "upload-image":
        asyncio.run(_cmd_upload_image(args))
    elif args.command == "serve" or args.command is None:
        uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
