from pathlib import Path
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from routers import report, setup


def _make_app(mock_service=None):
    app = FastAPI()
    static_dir = Path(__file__).resolve().parent.parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(setup.router)
    app.include_router(report.router)
    app.state.coverage_service = mock_service or _make_mock_service()
    app.state.base_url = ""
    return app


def _make_mock_service(**overrides):
    svc = Mock()
    svc.initialize = AsyncMock(return_value=True)
    svc.is_initialized = True
    svc.clear = Mock()
    svc.swagger_url = "http://example.com/swagger.json"
    svc.get_history = Mock(return_value=[])
    svc.total_count = 5
    svc.covered_count = 2
    svc.ratio = 0.4
    svc.spec = Mock()
    svc.spec.by_tag = {"api": []}
    svc.covered = set()
    svc.history_data = {}
    svc.mark = Mock()
    svc.record_request = Mock()
    for k, v in overrides.items():
        setattr(svc, k, v)
    return svc


class TestSetUrls:
    def test_success(self):
        mock_initialize = AsyncMock(return_value=True)
        mock_svc = _make_mock_service(initialize=mock_initialize)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post(
            "/set_urls",
            json={
                "base_url": "http://backend:8000",
                "swagger_url": "http://backend:8000/swagger.json",
            },
        )

        assert resp.status_code == 200
        assert resp.json() == {"message": "URLs успешно установлены"}

    def test_sets_base_url(self):
        mock_svc = _make_mock_service()
        app = _make_app(mock_svc)
        client = TestClient(app)

        client.post(
            "/set_urls",
            json={
                "base_url": "http://backend:8000",
                "swagger_url": "http://example.com/swagger.json",
            },
        )

        assert app.state.base_url == "http://backend:8000/"

    def test_returns_400_when_loader_fails(self):
        mock_initialize = AsyncMock(return_value=False)
        mock_svc = _make_mock_service(initialize=mock_initialize)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post(
            "/set_urls",
            json={
                "base_url": "http://backend:8000",
                "swagger_url": "http://bad-url.com/swagger.json",
            },
        )

        assert resp.status_code == 400
        assert "загрузить" in resp.json()["detail"]


class TestGetReport:
    def test_returns_url_form_when_not_initialized(self):
        mock_svc = _make_mock_service(is_initialized=False)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.get("/")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")

    def test_returns_coverage_when_initialized(self):
        mock_svc = _make_mock_service(is_initialized=True)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.get("/")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")


class TestExport:
    def test_returns_400_when_not_initialized(self):
        mock_svc = _make_mock_service(is_initialized=False)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.get("/export")

        assert resp.status_code == 400

    def test_returns_html_when_initialized(self):
        mock_svc = _make_mock_service(is_initialized=True)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.get("/export")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")


class TestClearCoverage:
    def test_returns_success_message(self):
        mock_svc = _make_mock_service()
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post("/clear_coverage")

        assert resp.json() == {"message": "Покрытие успешно очищено"}


class TestRefreshSpec:
    def test_returns_400_when_not_initialized(self):
        mock_svc = _make_mock_service(is_initialized=False)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post("/refresh_spec")

        assert resp.status_code == 400
        assert "загружена" in resp.json()["detail"]

    def test_returns_400_when_no_swagger_url(self):
        mock_svc = _make_mock_service(is_initialized=True, swagger_url="")
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post("/refresh_spec")

        assert resp.status_code == 400

    def test_success(self):
        mock_initialize = AsyncMock(return_value=True)
        mock_svc = _make_mock_service(initialize=mock_initialize)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post("/refresh_spec")

        assert resp.status_code == 200
        assert resp.json() == {"message": "Спецификация успешно обновлена"}

    def test_returns_400_when_reinitialize_fails(self):
        mock_initialize = AsyncMock(return_value=False)
        mock_svc = _make_mock_service(initialize=mock_initialize)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.post("/refresh_spec")

        assert resp.status_code == 400
        assert "обновить" in resp.json()["detail"]


class TestEndpointHistory:
    def test_returns_400_when_not_initialized(self):
        mock_svc = _make_mock_service(is_initialized=False)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.get("/endpoint_history?method=GET&path=/users")

        assert resp.status_code == 400

    def test_returns_records_as_json(self):
        mock_history = Mock(
            return_value=[
                Mock(
                    method="GET",
                    path="/users",
                    status_code=200,
                    timestamp="2024-01-01T00:00:00",
                    duration_ms=10.5,
                    query_params=None,
                    content_type="application/json",
                    request_preview=None,
                    response_preview=None,
                ),
            ]
        )
        mock_svc = _make_mock_service(get_history=mock_history)
        app = _make_app(mock_svc)
        client = TestClient(app)

        resp = client.get("/endpoint_history?method=GET&path=/users")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["method"] == "GET"
        assert data[0]["path"] == "/users"
        assert data[0]["status_code"] == 200
