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

- `src/main.py` — FastAPI app entrypoint. Proxies requests through `/proxy` mount using `fastapi-proxy-lib`. A middleware intercepts all requests and marks matching endpoints as covered.
- `src/core/coverage.py` — `CoverageService` dataclass: loads spec, tracks covered endpoints, computes coverage %.
- `src/core/loader.py` — Fetches the Swagger JSON via httpx.
- `src/core/parser.py` — Flattens `paths` into `{method, path}` lists; groups by tag.
- `src/core/utils.py` — `swagger_path_to_regex` converts `{param}` to named regex groups; `match_endpoint` handles `/proxy` prefix stripping and query param removal.

## Testing quirks

- Tests import from `src.core.*` directly (no conftest fixtures for db/network).
- Test runner: `task test` runs dead-fixtures check first, then `pytest --exitfirst --alluredir=allure-results --cov --cov-report=xml:cov.xml --cov-report=term-missing:skip-covered`.
- `pytest-deadfixtures` is a dev dependency — unused fixtures fail CI.
- Allure reports go to `allure-results/` (gitignored).

## Conventions

- Linter: ruff with default ruleset (no `pyproject.toml` tool.ruff section — uses ruff's defaults).
- Formatter: `ruff format` (not black). Run `task fmt` before committing.
- `package-mode = false` — this is an app, not a library.
- No type checker (mypy/pyright) configured.
- Template language: Russian UI labels; Bootstrap 5 + Font Awesome.
