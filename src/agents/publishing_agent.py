import json
import logging
from src.core.agent import Agent, AgentContext, AgentResult
from src.platforms import get_platform_adapter

logger = logging.getLogger(__name__)


class PublishingAgent(Agent):
    name = "PublishingAgent"
    role = "Especialista em publicação e agendamento de conteúdo"
    goal = (
        "Formatar, agendar e publicar conteúdo nas plataformas corretas, "
        "respeitando as regras e limites de cada rede social."
    )

    async def run(self, context: AgentContext) -> AgentResult:
        copies = context.metadata.get("CopyAgent", {}).get("copies", [])
        performance = context.metadata.get("PerformanceAgent", {})
        top_idx = performance.get("top_performer", 0)

        if not copies:
            return AgentResult(
                agent=self.name,
                success=False,
                output={},
                error="Nenhuma copy disponível para publicar.",
            )

        selected_copy = copies[top_idx] if top_idx < len(copies) else copies[0]
        platform = context.platform or "linkedin"

        adapter = get_platform_adapter(platform)
        if adapter is None:
            # Dry run — log what would be published
            logger.info(
                "PublishingAgent [dry-run] plataforma=%s copy=%s",
                platform,
                json.dumps(selected_copy, ensure_ascii=False)[:200],
            )
            return AgentResult(
                agent=self.name,
                success=True,
                output={
                    "status": "dry_run",
                    "platform": platform,
                    "selected_copy_index": top_idx,
                    "copy_preview": selected_copy,
                },
            )

        try:
            publish_result = await adapter.publish(selected_copy, context)
            return AgentResult(
                agent=self.name,
                success=True,
                output={"status": "published", "platform": platform, **publish_result},
            )
        except Exception as exc:
            logger.exception("PublishingAgent failed for platform %s", platform)
            return AgentResult(agent=self.name, success=False, output={}, error=str(exc))
