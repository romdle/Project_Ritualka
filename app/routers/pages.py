from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter() 

@router.get("/", response_class=HTMLResponse)
async def get_data(request: Request):
    return templates.TemplateResponse("glavnaya.html", {"request": request})

@router.get("/category/{name}")             
async def category(name: str):
    return f"Категория: {name}"

@router.get("/product/{name}")               
async def product(name: str):
    return {f"Страница товара №{name}": "work"}

@router.get("/info", response_class=HTMLResponse)
async def company(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})