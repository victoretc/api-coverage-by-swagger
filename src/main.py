import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

from core.loader import load_spec
from core.matcher import match_endpoint
from core.parser import parse_spec
from routers import report, setup
from services.coverage import CoverageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.coverage_service = CoverageService(
        loader=load_spec,
        parser=parse_spec,
        matcher=match_endpoint,
    )
    yield


app = FastAPI(title="API coverage tool", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(setup.router)
app.include_router(report.router)


@app.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy(request: Request, path: str):
    base = getattr(request.app.state, "base_url", None)
    if not base:
        raise HTTPException(status_code=400, detail="Base URL не настроен")

    start = time.monotonic()
    body = await request.body()
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(
            method=request.method,
            url=f"{base}{path}",
            headers=headers,
            content=body,
            params=request.query_params,
        )

    duration_ms = round((time.monotonic() - start) * 1000, 1)

    svc = request.app.state.coverage_service
    MAX_PREVIEW = 500
    svc.record_request(
        method=request.method,
        path=f"/proxy/{path}",
        status_code=resp.status_code,
        duration_ms=duration_ms,
        query_params=str(request.query_params) if request.query_params else None,
        content_type=resp.headers.get("content-type"),
        request_preview=(
            body[:MAX_PREVIEW].decode("utf-8", errors="replace") if body else None
        ),
        response_preview=(
            resp.content[:MAX_PREVIEW].decode("utf-8", errors="replace")
            if resp.content
            else None
        ),
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )


@app.middleware("http")
async def track_coverage(request: Request, call_next):
    response = await call_next(request)

    svc = request.app.state.coverage_service
    if svc.is_initialized and request.url.path.startswith("/proxy"):
        svc.mark(request.method, request.url.path)

    return response
