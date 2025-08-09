# syntax=docker/dockerfile:1.6

# Stage 1: Builder
FROM python:3.12-slim AS builder

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Create non-root user
RUN useradd -m -u 1001 appuser
USER appuser

ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
COPY --chown=appuser:appuser app app

EXPOSE 8080

# Security hardening
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health and timeout envs with sensible defaults
ENV REQUEST_TIMEOUT_S=10.0
ENV CACHE_TTL_S=60
ENV CACHE_MAXSIZE=512

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
