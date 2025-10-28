from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI()

@app.get("/")
async def get_data():
    path = os.path.join(os.path.dirname(__file__), "data", "data.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)

@app.get("/category/{name}")             # это ссылка под каталог, изначально будет открываться один, а дальше все остальные через кнопки в интерфейсе
async def category(name: str):
    return f"Категория: {name}"

@app.get("/product/{name}")               
async def product(name: str):
    return {f"Страница товара №{name}": "work"}

@app.get("/company")
async def print():
    return {"company" : "work"}

@app.get("/contacts")
async def print():
    return {"contacts" : "work"}



## запуск локалки через команду      uvicorn main:app --reload    в директории backend