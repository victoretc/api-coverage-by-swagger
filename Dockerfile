FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ARG POETRY_VERSION=1.8.5

RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir "poetry==$POETRY_VERSION"

ENV PATH="/venv/bin:$PATH" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry-cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

COPY src/ /app/src/
RUN poetry install --only main && rm -rf /tmp/poetry-cache

FROM builder AS development

RUN poetry install --no-root
COPY tests/ /app/tests/

FROM python:3.12-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

COPY --from=builder /venv /venv
COPY --from=builder /app /app

WORKDIR /app/src

USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
