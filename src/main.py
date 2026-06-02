"""
Social Content Agents — entrypoint principal.
Roda como API FastAPI ou como CLI.
"""

import asyncio
import json
import logging

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
        "copies": result.copies,
        "visuals": result.visuals,
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
            p: {"copies": r.copies, "visuals": r.visuals}
            for p, r in campaign.results.items()
        },
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

async def _cli_run():
    import sys

    topic = " ".join(sys.argv[1:]) or "Inteligência Artificial no marketing digital"
    logger.info("Gerando conteúdo para: %s", topic)

    await init_db()
    factory = ContentFactory()
    result = await factory.run(topic=topic, platform="linkedin", variations=2)

    print("\n" + "=" * 60)
    print(f"Tópico: {result.topic}")
    print(f"Plataforma: {result.platform}")
    print(f"Copies geradas: {len(result.copies)}")
    print("=" * 60)
    print(json.dumps(result.copies, ensure_ascii=False, indent=2))


def cli():
    asyncio.run(_cli_run())


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
