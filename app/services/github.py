from __future__ import annotations

from typing import Any

import httpx
from cachetools import TTLCache
from prometheus_client import Counter, Gauge
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from ..config import settings
from ..models.gist import Gist
import logging


class GitHubService:
    class UserNotFoundError(Exception):
        pass

    class DownstreamError(Exception):
        pass

    CACHE_HITS = Counter("github_cache_hits", "GitHub cache hits")
    CACHE_MISSES = Counter("github_cache_misses", "GitHub cache misses")
    CACHE_SIZE = Gauge("github_cache_size", "GitHub cache current size")
    CB_FAILURES = Counter("github_circuit_breaker_failures", "GitHub circuit breaker failures")
    CB_OPEN = Gauge("github_circuit_breaker_open", "GitHub circuit breaker open (1=open, 0=closed)")

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self._cache: TTLCache[tuple[str, int, int], list[Gist]] = TTLCache(
            maxsize=settings.cache_maxsize, ttl=settings.cache_ttl_s
        )
        self._cb_failures = 0
        self._cb_open = False

    async def _get_client(self) -> httpx.AsyncClient:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info(f"Settings: {settings!r}")

        if self._client is None:
            headers = {"Accept": "application/vnd.github+json", "User-Agent": settings.user_agent}
            if settings.github_token:
                headers["Authorization"] = f"Bearer {settings.github_token}"
            self._client = httpx.AsyncClient(headers=headers, timeout=settings.request_timeout_s)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(min=1, max=10))
    async def get_user_gists(self, user: str, page: int = 1, per_page: int = 30) -> list[Gist]:
        key = (user, page, per_page)
        if self._cb_open:
            self.CB_OPEN.set(1)
            raise self.DownstreamError("Circuit breaker is open")
        self.CB_OPEN.set(0)
        if key in self._cache:
            self.CACHE_HITS.inc()
            self.CACHE_SIZE.set(len(self._cache))
            return self._cache[key]
        self.CACHE_MISSES.inc()
        self.CACHE_SIZE.set(len(self._cache))

        client = await self._get_client()
        url = f"{settings.github_api_base}/users/{user}/gists"
        params = {"page": page, "per_page": per_page}
        try:
            resp = await client.get(url, params=params)
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            self._cb_failures += 1
            self.CB_FAILURES.inc()
            if self._cb_failures > 5:
                self._cb_open = True
                self.CB_OPEN.set(1)
            raise self.DownstreamError("GitHub API request failed") from exc

        if resp.status_code == 404:
            raise self.UserNotFoundError(f"User '{user}' not found")
        if resp.status_code >= 500:
            self._cb_failures += 1
            self.CB_FAILURES.inc()
            if self._cb_failures > 5:
                self._cb_open = True
                self.CB_OPEN.set(1)
            raise self.DownstreamError("GitHub API error")
        if resp.status_code != 200:
            self._cb_failures += 1
            self.CB_FAILURES.inc()
            if self._cb_failures > 5:
                self._cb_open = True
                self.CB_OPEN.set(1)
            raise self.DownstreamError(f"GitHub API unexpected status: {resp.status_code}")

        self._cb_failures = 0
        self._cb_open = False
        self.CB_OPEN.set(0)
        data: list[dict[str, Any]] = resp.json()
        gists = [Gist.from_api(item) for item in data]
        self._cache[key] = gists
        self.CACHE_SIZE.set(len(self._cache))
        return gists

    async def count_user_gists(self, user: str) -> int:
        client = await self._get_client()
        url = f"{settings.github_api_base}/users/{user}/gists"
        try:
            resp = await client.get(url)
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise self.DownstreamError("GitHub API request failed") from exc

        if resp.status_code == 404:
            raise self.UserNotFoundError(f"User '{user}' not found")
        if resp.status_code >= 500:
            raise self.DownstreamError("GitHub API error")
        if resp.status_code != 200:
            raise self.DownstreamError(f"GitHub API unexpected status: {resp.status_code}")

        data: list[dict[str, Any]] = resp.json()
        return len(data)
