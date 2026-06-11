from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def get_report(request: Request):
    svc = request.app.state.coverage_service
    if not svc.is_initialized:
        return templates.TemplateResponse("url_form.html", {"request": request})

    state = svc.state
    return templates.TemplateResponse(
        "coverage.html",
        {
            "request": request,
            "total_endpoints": state.total_count,
            "covered_endpoints_count": state.covered_count,
            "coverage_percentage": round(state.ratio * 100, 2),
            "endpoints_by_tags": state.spec.by_tag,
            "tags": list(state.spec.by_tag),
            "covered_endpoints": state.covered,
        },
    )


@router.post("/clear_coverage")
async def clear_coverage(request: Request):
    request.app.state.coverage_service.clear()
    return {"message": "Покрытие успешно очищено"}


@router.post("/refresh_spec")
async def refresh_spec(request: Request):
    svc = request.app.state.coverage_service
    if not svc.state or not svc.state.swagger_url:
        raise HTTPException(
            status_code=400,
            detail="Спецификация не загружена",
        )

    if not await svc.initialize(svc.state.swagger_url):
        raise HTTPException(
            status_code=400,
            detail="Не удалось обновить спецификацию",
        )

    return {"message": "Спецификация успешно обновлена"}
