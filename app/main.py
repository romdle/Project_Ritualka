from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from pathlib import Path

from routers import admin, pages

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/scripts", StaticFiles(directory=BASE_DIR / "scripts"), name="scripts")

app.include_router(pages.router)
app.include_router(admin.router)







## запуск локалки через команду      uvicorn main:app --reload    в директории app\