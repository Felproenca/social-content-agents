"""
CampaignBuilder: gera uma campanha completa de conteúdo para múltiplas plataformas.
"""

from dataclasses import dataclass, field
from src.workflows.content_factory import ContentFactory, ContentFactoryResult


@dataclass
class Campaign:
    name: str
    topic: str
    platforms: list[str]
    results: dict[str, ContentFactoryResult] = field(default_factory=dict)

    @property
    def total_copies(self) -> int:
        return sum(len(r.copies) for r in self.results.values())


class CampaignBuilder:
    def __init__(self):
        self.factory = ContentFactory()

    async def build(
        self,
        name: str,
        topic: str,
        platforms: list[str],
        tone: str = "thought_leader",
        audience: str = "",
        variations_per_platform: int = 2,
    ) -> Campaign:
        campaign = Campaign(name=name, topic=topic, platforms=platforms)

        for platform in platforms:
            result = await self.factory.run(
                topic=topic,
                platform=platform,
                tone=tone,
                audience=audience,
                variations=variations_per_platform,
            )
            campaign.results[platform] = result

        return campaign
