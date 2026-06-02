"""
AutoPublish: executa ContentFactory com publicação automática habilitada.
Wrapper de conveniência para uso em agendadores (cron, Celery, etc.).
"""

import logging
from src.workflows.content_factory import ContentFactory, ContentFactoryResult

logger = logging.getLogger(__name__)


class AutoPublish:
    def __init__(self):
        self.factory = ContentFactory()

    async def publish_now(
        self,
        topic: str,
        platform: str,
        tone: str = "professional",
        audience: str = "",
    ) -> ContentFactoryResult:
        logger.info("AutoPublish iniciado: topic=%s platform=%s", topic, platform)
        result = await self.factory.run(
            topic=topic,
            platform=platform,
            tone=tone,
            audience=audience,
            auto_publish=True,
        )
        logger.info(
            "AutoPublish concluído: copies=%d publish_status=%s",
            len(result.copies),
            result.publish_status.get("status"),
        )
        return result
