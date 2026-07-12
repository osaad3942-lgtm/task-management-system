from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.utils.metrics import get_metrics

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/monitoring")
def monitoring_api():
    return get_metrics()


@router.get("/dashboard", response_class=HTMLResponse)
def monitoring_dashboard(request: Request):
    metrics = get_metrics()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"metrics": metrics}
    )