from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from pathlib import Path

from routers import admin, pages

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/scripts", StaticFiles(directory=BASE_DIR / "scripts"), name="scripts")

app.include_router(pages.router)
app.include_router(admin.router)


def _should_redirect(request: Request) -> bool:
    if request.url.path.startswith("/api"):
        return False
    return request.method.upper() in {"GET", "HEAD"}


async def _handle_http_exception(
    request: Request, exc: StarletteHTTPException
):
    if exc.status_code == status.HTTP_404_NOT_FOUND and _should_redirect(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return await http_exception_handler(request, exc)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    return await _handle_http_exception(request, exc)


@app.exception_handler(FastAPIHTTPException)
async def fastapi_http_exception_handler(
    request: Request, exc: FastAPIHTTPException
):
    return await _handle_http_exception(request, exc)






## запуск локалки через команду      uvicorn main:app --reload    в директории app\