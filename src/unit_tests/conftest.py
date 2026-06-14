from pathlib import Path

import pytest
from fastapi.templating import Jinja2Templates


@pytest.fixture(autouse=True)
def _patch_templates(monkeypatch):
    from routers import report

    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    monkeypatch.setattr(
        report,
        "templates",
        Jinja2Templates(directory=str(templates_dir)),
    )
