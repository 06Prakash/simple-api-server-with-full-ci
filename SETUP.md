# Project Setup and Usage – EE Gists API

This guide shows how to set up, run, test, and containerize the FastAPI service that lists a user’s public GitHub gists.

## Overview

- Tech: FastAPI, httpx, Pydantic, pytest, respx
- Endpoint: `GET /{user}?page=&per_page=` returns public gists
- Health: `GET /health`
- Port: 8080

## Prerequisites

- Python 3.10+ (3.12 recommended) and pip
- Docker (optional, for container run)

## Quickstart (Docker)

1) Build image
   - docker build -t ee-gists-api:local .
2) Run
   - docker run --rm -p 8080:8080 ee-gists-api:local
3) Verify
   - Health: <http://localhost:8080/health>
   - Example: <http://localhost:8080/octocat?page=1&per_page=2>

Environment variables (optional):

- GITHUB_TOKEN – increase GitHub API rate limits.
- REQUEST_TIMEOUT_S (default 10.0)
- CACHE_TTL_S (default 60)
- CACHE_MAXSIZE (default 512)

Example with token:

- docker run --rm -e GITHUB_TOKEN=ghp_xxx -p 8080:8080 ee-gists-api:local

## Quickstart (Local Dev)

Windows PowerShell:

1) Create and activate venv
   - python -m venv .venv
   - . .venv/Scripts/Activate.ps1
2) Upgrade tools (recommended)
   - python -m pip install --upgrade "pip>=23.1" "setuptools>=61,<70" wheel
3) Install deps (dev)
   - pip install -e .[dev]
   - If build isolation is restricted, alternatively: pip install -r requirements.txt
4) Run API
   - uvicorn app.main:app --reload --port 8080

macOS/Linux (bash):

1) python3 -m venv .venv
2) source .venv/bin/activate
3) python -m pip install --upgrade "pip>=23.1" "setuptools>=61,<70" wheel
4) pip install -e .[dev]
5) uvicorn app.main:app --reload --port 8080

## Tests and Coverage

- Run tests: pytest
- Coverage threshold enforced at 98%+ (configured in pyproject.toml).

## Lint and Type Check

- Ruff: ruff check .
- Mypy: mypy app

## API Summary

- GET /{user} – list gists
  - Query: page (int, default 1), per_page (int, default 30)
  - Errors: 404 (user not found), 502 (downstream error)
- GET /health – service health

## CI/CD

- GitHub Actions workflow at .github/workflows/ci.yml runs lint, type-check, tests (coverage ≥98%), and docker build on push/PR.

## Troubleshooting

- Editable install errors (setuptools): upgrade pip/setuptools as shown above.
- Rate limits: pass GITHUB_TOKEN env.
> **Note:** If PowerShell scripts are blocked by your organization's policies, run PowerShell as administrator and set the execution policy for the current process: (If you have admin rights)
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
> ```
