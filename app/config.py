from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    github_api_base: str = "https://api.github.com"
    request_timeout_s: float = 10.0
    cache_ttl_s: int = 60
    cache_maxsize: int = 512
    user_agent: str = "ee-gists-api/0.1.0"
    github_token: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            github_api_base=os.getenv("GITHUB_API_BASE", defaults.github_api_base),
            request_timeout_s=float(os.getenv("REQUEST_TIMEOUT_S", defaults.request_timeout_s)),
            cache_ttl_s=int(os.getenv("CACHE_TTL_S", defaults.cache_ttl_s)),
            cache_maxsize=int(os.getenv("CACHE_MAXSIZE", defaults.cache_maxsize)),
            user_agent=os.getenv("USER_AGENT", defaults.user_agent),
            github_token=os.getenv("GITHUB_TOKEN"),
        )



settings = Settings.from_env()
