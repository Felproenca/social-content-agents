import httpx
from src.core.config import settings
from src.core.agent import AgentContext

GRAPH_API = "https://graph.facebook.com/v21.0"


class InstagramAdapter:
    def __init__(self):
        self._token = settings.meta_access_token

    async def publish(self, copy: dict, context: AgentContext) -> dict:
        if not self._token:
            raise RuntimeError("META_ACCESS_TOKEN não configurado.")

        caption = (
            f"{copy.get('hook', '')}\n\n{copy.get('body', '')}\n\n{copy.get('cta', '')}"
        )
        hashtags = " ".join(copy.get("hashtags", []))
        full_caption = f"{caption}\n\n{hashtags}"[:2200]

        # Instagram requires an image — stub returns dry-run
        return {"status": "dry_run", "caption_preview": full_caption[:100]}
