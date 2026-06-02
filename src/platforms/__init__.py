from src.platforms.linkedin import LinkedInAdapter
from src.platforms.instagram import InstagramAdapter
from src.platforms.tiktok import TikTokAdapter
from src.platforms.youtube import YouTubeAdapter
from src.platforms.x_twitter import XTwitterAdapter

_ADAPTERS = {
    "linkedin": LinkedInAdapter,
    "instagram": InstagramAdapter,
    "tiktok": TikTokAdapter,
    "youtube": YouTubeAdapter,
    "x_twitter": XTwitterAdapter,
    "twitter": XTwitterAdapter,
}


def get_platform_adapter(platform: str):
    cls = _ADAPTERS.get(platform.lower())
    if cls is None:
        return None
    try:
        return cls()
    except Exception:
        return None
