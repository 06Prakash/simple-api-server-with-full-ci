from fastapi import APIRouter, HTTPException, Depends

from ..services.github import GitHubService
from ..models.gist import Gist
from .dependencies import get_service

router = APIRouter()


@router.get("/{user}", response_model=list[Gist], tags=["gists"])
async def list_gists(user: str, page: int = 1, per_page: int = 30, svc: GitHubService = Depends(get_service)) -> list[Gist]:
    """
    Return the public gists for a user. Supports optional pagination parameters.
    """
    try:
        return await svc.get_user_gists(user=user, page=page, per_page=per_page)
    except GitHubService.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GitHubService.DownstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
