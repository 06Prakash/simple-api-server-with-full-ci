# EE Gists API – Code Walkthrough

This walkthrough provides an overview of the FastAPI-based GitHub Gists API project, focusing on architecture, flow, and DevOps-relevant aspects.

## 1. Project Structure
- `app/` – Main application code
  - `main.py` – FastAPI app setup, health check, router inclusion, and graceful shutdown
  - `config.py` – Centralized configuration using Pydantic, supports environment overrides
  - `api/` – API layer
    - `routes.py` – Defines API endpoints, including `/favicon.ico` and `/[user]` for gist listing
    - `dependencies.py` – Dependency injection for service layer
  - `models/` – Data models
    - `gist.py` – Pydantic models for Gist and GistFile, with API payload parsing
  - `services/` – Service layer
    - `github.py` – Handles GitHub API requests, caching, error handling
- `tests/` – Unit and integration tests
- `Dockerfile` – Multi-stage build for secure, reproducible containerization
- `pyproject.toml` – Project metadata, dependencies, and tooling

## 2. API Flow
- **Entry Point:** `main.py` creates the FastAPI app, includes health check and gist router.
- **Routing:** `routes.py` exposes `/[user]` endpoint, supporting pagination (`page`, `per_page`).
- **Dependency Injection:** `dependencies.py` provides a singleton `GitHubService` instance.
- **Service Layer:** `github.py` fetches gists from GitHub, applies caching, and handles errors.
- **Models:** `gist.py` parses and validates API responses into Pydantic models.

## 3. Caching & Configuration
- **Caching:** Uses `cachetools.TTLCache` in `GitHubService` to reduce API calls and improve performance. Cache size and TTL are configurable.
- **Configuration:** `config.py` loads settings from environment variables, supporting overrides for API base URL, timeouts, cache, and authentication.

## 4. Docker Setup
- **Multi-stage Build:**
  - Stage 1: Installs dependencies in a virtual environment
  - Stage 2: Runs as non-root user for security, copies app code and venv
- **Environment Variables:** Exposes settings for timeout, cache, etc.
- **Entrypoint:** Runs Uvicorn server on port 8080

## 5. Testing & Tooling
- **Tests:** Located in `tests/`, covering API, service, and integration logic
- **Tooling:** Uses `pytest`, `mypy`, `ruff`, and coverage tools for quality assurance
- **CI:** GitHub Actions workflow in `.github/workflows/ci.yml` for automated testing

## 6. DevOps Considerations
- **Health Check:** `/health` endpoint for readiness/liveness probes
- **Configurable via ENV:** Easy to tune for different environments
- **Secure Container:** Non-root user, disables bytecode writes, unbuffered output
- **Extensible:** Modular design for adding more endpoints or services

---
This structure ensures maintainability, scalability, and operational robustness, aligning with best practices for cloud-native Python APIs.
