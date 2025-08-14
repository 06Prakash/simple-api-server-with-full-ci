from fastapi import APIRouter, Depends, HTTPException, Response

from ..models.gist import Gist
from ..services.github import GitHubService
from .dependencies import get_service
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ignore favicon.ico requests
@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

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

@router.get("/{user}/count", response_model=int, tags=["gists"])
async def count_gists(user: str, svc: GitHubService = Depends(get_service)) -> int:
    """
    Return the count of public gists for a user.
    """
    try:
        logger.info(f"Counting gists for user: {user}")
        if not user:
            raise HTTPException(status_code=400, detail="Username must be provided")
        return await svc.count_user_gists(user=user)
    except GitHubService.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GitHubService.DownstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc