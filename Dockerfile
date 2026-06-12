# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.5

RUN groupadd -r app && \
    useradd -r -g app -d /app -s /sbin/nologin app

FROM base AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry-cache \
    POETRY_NO_INTERACTION=1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --only main --no-interaction --no-ansi && \
    rm -rf /tmp/poetry-cache

COPY src/ ./src/

RUN poetry install --only main --no-interaction --no-ansi && \
    rm -rf /tmp/poetry-cache

FROM builder AS development

RUN poetry install --no-interaction --no-ansi

COPY tests/ ./tests/
COPY .env.example .env 2>/dev/null || true

USER app

FROM base AS production

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/src /app/logs /app/media /app/static && \
    chown -R app:app /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/

RUN chown -R app:app /app

USER app


EXPOSE 8000

WORKDIR /app/src
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8000"]