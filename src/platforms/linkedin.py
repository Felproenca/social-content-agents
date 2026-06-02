import httpx
from src.core.config import settings
from src.core.agent import AgentContext

LINKEDIN_API = "https://api.linkedin.com/v2"


class LinkedInAdapter:
    def __init__(self):
        self._token = settings.linkedin_access_token

    async def publish(self, copy: dict, context: AgentContext) -> dict:
        if not self._token:
            raise RuntimeError("LINKEDIN_ACCESS_TOKEN não configurado.")

        text = f"{copy.get('hook', '')}\n\n{copy.get('body', '')}\n\n{copy.get('cta', '')}"

        payload = {
            "author": "urn:li:person:ME",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text[:3000]},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LINKEDIN_API}/ugcPosts",
                json=payload,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=30,
            )
            response.raise_for_status()
            return {"post_id": response.headers.get("x-restli-id"), "url": ""}
