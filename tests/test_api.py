from fastapi.testclient import TestClient

from app.main import app
from app.models.gist import Gist, GistFile
from app.services.github import GitHubService
import app.api.dependencies as deps


class FakeService(GitHubService):
    def __init__(self, data: list[Gist] | Exception):
        super().__init__(client=None)
        self._data = data
        self.calls = []

    async def get_user_gists(self, user: str, page: int = 1, per_page: int = 30):
        self.calls.append((user, page, per_page))
        if isinstance(self._data, Exception):
            raise self._data
        return self._data


def override_service(service: GitHubService):
    app.dependency_overrides[deps.get_service] = lambda: service


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_gists_success():
    data = [
        Gist(id="1", description="desc", html_url="https://gist.github.com/1", files=[
            GistFile(filename="a.py", language="Python", raw_url="https://gist.githubusercontent.com/raw/1", size=10)
        ])
    ]
    svc = FakeService(data)
    override_service(svc)
    client = TestClient(app)
    r = client.get("/octocat?page=2&per_page=5")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list) and len(body) == 1
    assert svc.calls == [("octocat", 2, 5)]
    assert body[0]["id"] == "1"
    assert body[0]["files"][0]["filename"] == "a.py"


def test_list_gists_user_not_found():
    svc = FakeService(GitHubService.UserNotFoundError("User 'nope' not found"))
    override_service(svc)
    client = TestClient(app)
    r = client.get("/nope")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_list_gists_downstream_error():
    svc = FakeService(GitHubService.DownstreamError("boom"))
    override_service(svc)
    client = TestClient(app)
    r = client.get("/octocat")
    assert r.status_code == 502


def test_bad_request_username():
    client = TestClient(app)
    r = client.get("//")  # empty user before first slash
    # FastAPI will normalize route; ensure our 404 path is not hit here
    assert r.status_code in (404, 422)


def test_validation_error_query_params():
    client = TestClient(app)
    # per_page as string should be 422
    r = client.get("/octocat?per_page=abc")
    assert r.status_code == 422


def test_app_lifespan_shutdown_close_client(monkeypatch):
    called = {"closed": False}

    class Dummy(GitHubService):
        async def close(self) -> None:  # type: ignore[override]
            called["closed"] = True

    app.dependency_overrides[deps.get_service] = lambda: Dummy()
    with TestClient(app) as client:
        client.get("/health")
    assert called["closed"] is True


def test_model_from_api():
    payload = {
        "id": "abc",
        "description": None,
        "html_url": "https://gist.github.com/abc",
        "files": {
            "file1": {
                "filename": "file1.py",
                "language": "Python",
                "raw_url": "https://gist.githubusercontent.com/raw/file1",
                "size": 123,
            }
        },
    }
    g = Gist.from_api(payload)
    assert g.id == "abc"
    assert g.files[0].filename == "file1.py"


def test_model_from_api_ignores_null_files():
    payload = {
        "id": "abc",
        "html_url": "https://gist.github.com/abc",
        "files": {"bad": None, "no_raw": {"filename": "x"}},
    }
    g = Gist.from_api(payload)
    # no valid files collected
    assert g.files == []
