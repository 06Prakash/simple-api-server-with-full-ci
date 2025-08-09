from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from .api.dependencies import get_service
from .api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: no special action
    yield
    # Shutdown: close service HTTP client
    # Respect FastAPI dependency overrides in tests
    svc_factory = app.dependency_overrides.get(get_service, get_service)
    svc = svc_factory()
    await svc.close()

app = FastAPI(title="EE Gists API", version="0.1.0", lifespan=lifespan)

@app.get("/health", tags=["health"])  # tiny health check
async def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(router)
