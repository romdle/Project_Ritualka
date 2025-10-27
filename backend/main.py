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



## запуск локалки через команду      uvicorn backend.main:app --reload    в директории project