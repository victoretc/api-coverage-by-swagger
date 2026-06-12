from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def get_report(request: Request):
    svc = request.app.state.coverage_service
    if not svc.is_initialized:
        return templates.TemplateResponse(
            request, "url_form.html", {"request": request}
        )

    return templates.TemplateResponse(
        request,
        "coverage.html",
        {
            "request": request,
            "total_endpoints": svc.total_count,
            "covered_endpoints_count": svc.covered_count,
            "coverage_percentage": round(svc.ratio * 100, 2),
            "endpoints_by_tags": svc.spec.by_tag,
            "tags": list(svc.spec.by_tag),
            "covered_endpoints": svc.covered,
        },
    )


@router.get("/export", response_class=HTMLResponse)
async def export_report(request: Request):
    svc = request.app.state.coverage_service
    if not svc.is_initialized:
        raise HTTPException(status_code=400, detail="Спецификация не загружена")

    return templates.TemplateResponse(
        request,
        "report_export.html",
        {
            "request": request,
            "total_endpoints": svc.total_count,
            "covered_endpoints_count": svc.covered_count,
            "coverage_percentage": round(svc.ratio * 100, 2),
            "endpoints_by_tags": svc.spec.by_tag,
            "tags": list(svc.spec.by_tag),
            "covered_endpoints": svc.covered,
        },
    )


@router.post("/clear_coverage")
async def clear_coverage(request: Request):
    request.app.state.coverage_service.clear()
    return {"message": "Покрытие успешно очищено"}


@router.post("/refresh_spec")
async def refresh_spec(request: Request):
    svc = request.app.state.coverage_service
    if not svc.is_initialized or not svc.swagger_url:
        raise HTTPException(
            status_code=400,
            detail="Спецификация не загружена",
        )

    if not await svc.initialize(svc.swagger_url):
        raise HTTPException(
            status_code=400,
            detail="Не удалось обновить спецификацию",
        )

    return {"message": "Спецификация успешно обновлена"}


@router.get("/endpoint_history")
async def endpoint_history(
    request: Request,
    method: str = Query(),
    path: str = Query(),
):
    svc = request.app.state.coverage_service
    if not svc.is_initialized:
        raise HTTPException(status_code=400, detail="Спецификация не загружена")
    records = svc.get_history(method, path)
    return JSONResponse(
        content=[
            {
                "method": r.method,
                "path": r.path,
                "status_code": r.status_code,
                "timestamp": r.timestamp,
                "duration_ms": r.duration_ms,
                "query_params": r.query_params,
                "content_type": r.content_type,
                "request_preview": r.request_preview,
                "response_preview": r.response_preview,
            }
            for r in records
        ]
    )
