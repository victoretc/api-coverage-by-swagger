from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class CoverageSetup(BaseModel):
    base_url: str
    swagger_url: str


@router.post("/set_urls")
async def setup_coverage(data: CoverageSetup, request: Request):
    svc = request.app.state.coverage_service
    if not await svc.initialize(data.swagger_url):
        raise HTTPException(
            status_code=400,
            detail="Не удалось загрузить спецификацию Swagger",
        )

    request.app.state.base_url = data.base_url.rstrip("/") + "/"
    return {"message": "URLs успешно установлены"}
