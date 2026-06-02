from src.core.config import settings
from src.core.agent import AgentContext


class YouTubeAdapter:
    def __init__(self):
        self._client_id = settings.youtube_client_id

    async def publish(self, copy: dict, context: AgentContext) -> dict:
        if not self._client_id:
            raise RuntimeError("YOUTUBE_CLIENT_ID não configurado.")
        # YouTube requires OAuth2 + video file — stub for now
        return {"status": "dry_run", "note": "YouTube requer OAuth2 e upload de vídeo."}
