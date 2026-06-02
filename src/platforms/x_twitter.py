import httpx
from src.core.config import settings
from src.core.agent import AgentContext

TWITTER_API = "https://api.twitter.com/2"


class XTwitterAdapter:
    def __init__(self):
        self._token = settings.twitter_access_token

    async def publish(self, copy: dict, context: AgentContext) -> dict:
        if not self._token:
            raise RuntimeError("TWITTER_ACCESS_TOKEN não configurado.")

        hook = copy.get("hook", "")
        text = hook[:280]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TWITTER_API}/tweets",
                json={"text": text},
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {"tweet_id": data.get("data", {}).get("id"), "text": text}
