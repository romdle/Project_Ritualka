from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from routers import pages

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)







## запуск локалки через команду      uvicorn main:app --reload    в директории app\