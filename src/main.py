from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_proxy_lib.fastapi.app import reverse_http_app
import httpx

from pydantic import BaseModel
from core.coverage import CoverageService

app = FastAPI(title="API coverage tool")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

coverage_service = CoverageService()


class CoverageSetup(BaseModel):
    base_url: str
    swagger_url: str


@app.post("/set_urls")
async def setup_coverage(data: CoverageSetup):
    if not coverage_service.initialize(data.swagger_url):
        raise HTTPException(
            status_code=400, detail="Не удалось загрузить спецификацию Swagger"
        )

    if not data.base_url.endswith("/"):
        data.base_url += "/"

    client = httpx.AsyncClient(timeout=10)
    app.mount("/proxy", reverse_http_app(base_url=data.base_url, client=client))

    return {"message": "URLs успешно установлены"}


@app.middleware("http")
async def track_coverage(request: Request, call_next):
    response = await call_next(request)

    if coverage_service.is_initialized:
        method = request.method
        path = request.url.path
        coverage_service.mark_covered(method, path)

    return response


@app.post("/clear_coverage")
def reset_coverage():
    coverage_service.clear_coverage()
    return {"message": "Покрытие успешно очищено"}


@app.post("/refresh_spec")
async def refresh_spec():
    if not coverage_service.initialize(coverage_service._current_swagger_url):
        raise HTTPException(
            status_code=400,
            detail="Не удалось обновить спецификацию",
        )

    return {"message": "Спецификация успешно обновлена"}


@app.get("/", response_class=HTMLResponse)
def get_coverage_report(request: Request):
    if not coverage_service.is_initialized:
        return templates.TemplateResponse("url_form.html", {"request": request})

    return templates.TemplateResponse(
        "coverage.html",
        {"request": request, **coverage_service.get_coverage_data()},
    )
