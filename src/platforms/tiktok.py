from src.core.config import settings
from src.core.agent import AgentContext


class TikTokAdapter:
    def __init__(self):
        self._token = settings.tiktok_access_token

    async def publish(self, copy: dict, context: AgentContext) -> dict:
        if not self._token:
            raise RuntimeError("TIKTOK_ACCESS_TOKEN não configurado.")
        # TikTok requires video upload — stub for now
        return {"status": "dry_run", "note": "TikTok requer upload de vídeo via API."}
