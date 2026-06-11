# api-coverage-by-swagger

FastAPI app that tracks endpoint coverage against a Swagger/OpenAPI spec.

## Quick start

```bash
task install-deps    # poetry install
task run             # uvicorn on :8000
task lint            # ruff check .
task fmt             # ruff check --fix + ruff format
task test            # dead-fixtures check, then pytest with allure + cov
```

## Architecture

- `src/main.py` — FastAPI app entrypoint, lifespan wiring, middleware, inline reverse-proxy route over httpx.
- `src/models.py` — `Endpoint`, `ParsedSpec`, `CoverageState` dataclasses.
- `src/core/loader.py` — Fetches the Swagger JSON via async httpx.
- `src/core/parser.py` — Parses spec into `ParsedSpec` (typed endpoints + tag groups).
- `src/core/matcher.py` — `EndpointMatcher` with `@lru_cache`-ed regex compilation.
- `src/services/coverage.py` — `CoverageService` with DI: receives loader, parser, matcher. No global state.
- `src/routers/setup.py` — `POST /set_urls`.
- `src/routers/report.py` — `GET /`, `POST /clear_coverage`, `POST /refresh_spec`.

## Testing quirks

- Tests import from `src.*` directly (no conftest fixtures for db/network).
- Test runner: `task test` runs dead-fixtures check first, then `pytest --exitfirst --alluredir=allure-results --cov --cov-report=xml:cov.xml --cov-report=term-missing:skip-covered`.
- `pytest-deadfixtures` is a dev dependency — unused fixtures fail CI.
- Allure reports go to `allure-results/` (gitignored).

## Conventions

- Linter: ruff with default ruleset (no `pyproject.toml` tool.ruff section — uses ruff's defaults).
- Formatter: `ruff format` (not black). Run `task fmt` before committing.
- `package-mode = false` — this is an app, not a library.
- No type checker (mypy/pyright) configured.
- Template language: Russian UI labels; Bootstrap 5 + Font Awesome.
