from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

from core.loader import load_spec
from core.matcher import EndpointMatcher
from core.parser import parse_spec
from routers import report, setup
from services.coverage import CoverageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.coverage_service = CoverageService(
        loader=load_spec,
        parser=parse_spec,
        matcher=EndpointMatcher(),
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
