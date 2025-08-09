from __future__ import annotations

from ..services.github import GitHubService

_service: GitHubService | None = None


def get_service() -> GitHubService:
    global _service
    if _service is None:
        _service = GitHubService()
    return _service
