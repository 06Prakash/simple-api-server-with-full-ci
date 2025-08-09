import pytest
import respx

from app.api import dependencies as deps
from app.config import settings
from app.services.github import GitHubService


def test_dependency_lazy_init_and_cache(monkeypatch):
    # Reset global service
    deps._service = None  # type: ignore[attr-defined]
    a = deps.get_service()
    b = deps.get_service()
    assert isinstance(a, GitHubService)
    assert a is b  # cached singleton


@pytest.mark.asyncio
async def test_client_headers_and_close(monkeypatch):
    svc = GitHubService()
    token_before = settings.github_token
    settings.github_token = "secret-token"
    try:
        client = await svc._get_client()  # type: ignore[attr-defined]
        # Authorization header is set when token present
        assert client.headers.get("Authorization") == "Bearer secret-token"
        # Close path when client exists
        assert not client.is_closed
        await svc.close()
        assert client.is_closed
    finally:
        settings.github_token = token_before


@pytest.mark.asyncio
async def test_pagination_affects_cache(monkeypatch):
    svc = GitHubService()
    base = settings.github_api_base
    user = "octocat"
    with respx.mock(base_url=base) as respx_mock:
        respx_mock.get(f"/users/{user}/gists").respond(status_code=200, json=[])
        await svc.get_user_gists(user, page=1, per_page=10)
        # New call for a different page
        respx_mock.get(f"/users/{user}/gists").respond(status_code=200, json=[])
        await svc.get_user_gists(user, page=2, per_page=10)
