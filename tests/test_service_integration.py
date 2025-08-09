import json
from http import HTTPStatus

import pytest
import respx
import httpx

from app.services.github import GitHubService
from app.config import settings


@pytest.mark.asyncio
async def test_service_fetches_and_maps(monkeypatch):
    svc = GitHubService()
    base = settings.github_api_base
    user = "octocat"
    route = f"{base}/users/{user}/gists"
    mock_data = [
        {
            "id": "1",
            "description": "d",
            "html_url": "https://gist.github.com/1",
            "files": {
                "a": {
                    "filename": "a.py",
                    "language": "Python",
                    "raw_url": "https://gist.githubusercontent.com/raw/a",
                    "size": 1,
                }
            },
        }
    ]
    with respx.mock(base_url=base) as respx_mock:
        respx_mock.get(f"/users/{user}/gists").respond(
            status_code=HTTPStatus.OK, json=mock_data
        )
        gists = await svc.get_user_gists(user)
        assert len(gists) == 1
        assert gists[0].id == "1"


@pytest.mark.asyncio
async def test_service_404_to_user_not_found():
    svc = GitHubService()
    base = settings.github_api_base
    user = "nope"
    with respx.mock(base_url=base) as respx_mock:
        respx_mock.get(f"/users/{user}/gists").respond(status_code=HTTPStatus.NOT_FOUND)
        with pytest.raises(GitHubService.UserNotFoundError):
            await svc.get_user_gists(user)


@pytest.mark.asyncio
async def test_service_cache(monkeypatch):
    svc = GitHubService()
    base = settings.github_api_base
    user = "octocat"
    with respx.mock(base_url=base) as respx_mock:
        call = respx_mock.get(f"/users/{user}/gists").respond(status_code=200, json=[])
        a = await svc.get_user_gists(user)
        b = await svc.get_user_gists(user)
        assert a == b
        # Only one HTTP call due to cache
        assert call.called
        assert call.call_count == 1


@pytest.mark.asyncio
async def test_service_500_error():
    svc = GitHubService()
    base = settings.github_api_base
    user = "octocat"
    with respx.mock(base_url=base) as respx_mock:
        respx_mock.get(f"/users/{user}/gists").respond(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        with pytest.raises(GitHubService.DownstreamError):
            await svc.get_user_gists(user)


@pytest.mark.asyncio
async def test_service_unexpected_status():
    svc = GitHubService()
    base = settings.github_api_base
    user = "octocat"
    with respx.mock(base_url=base) as respx_mock:
        respx_mock.get(f"/users/{user}/gists").respond(status_code=HTTPStatus.UNAUTHORIZED)
        with pytest.raises(GitHubService.DownstreamError):
            await svc.get_user_gists(user)


@pytest.mark.asyncio
async def test_service_request_error():
    svc = GitHubService()
    base = settings.github_api_base
    user = "octocat"
    with respx.mock(base_url=base) as respx_mock:
        # Raise a request-level error from httpx
        respx_mock.get(f"/users/{user}/gists").mock(
            side_effect=httpx.RequestError("boom", request=httpx.Request("GET", f"{base}/users/{user}/gists"))
        )
        with pytest.raises(GitHubService.DownstreamError):
            await svc.get_user_gists(user)
