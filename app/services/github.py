from __future__ import annotations

from typing import Any

import httpx
from cachetools import TTLCache

from ..config import settings
from ..models.gist import Gist


class GitHubService:
    class UserNotFoundError(Exception):
        pass

    class DownstreamError(Exception):
        pass

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self._cache: TTLCache[tuple[str, int, int], list[Gist]] = TTLCache(
            maxsize=settings.cache_maxsize, ttl=settings.cache_ttl_s
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/vnd.github+json", "User-Agent": settings.user_agent}
            if settings.github_token:
                headers["Authorization"] = f"Bearer {settings.github_token}"
            self._client = httpx.AsyncClient(headers=headers, timeout=settings.request_timeout_s)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def get_user_gists(self, user: str, page: int = 1, per_page: int = 30) -> list[Gist]:
        key = (user, page, per_page)
        if key in self._cache:
            return self._cache[key]

        client = await self._get_client()
        url = f"{settings.github_api_base}/users/{user}/gists"
        params = {"page": page, "per_page": per_page}
        try:
            resp = await client.get(url, params=params)
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise self.DownstreamError("GitHub API request failed") from exc

        if resp.status_code == 404:
            raise self.UserNotFoundError(f"User '{user}' not found")
        if resp.status_code >= 500:
            raise self.DownstreamError("GitHub API error")
        if resp.status_code != 200:
            raise self.DownstreamError(f"GitHub API unexpected status: {resp.status_code}")

        data: list[dict[str, Any]] = resp.json()
        gists = [Gist.from_api(item) for item in data]
        self._cache[key] = gists
        return gists
