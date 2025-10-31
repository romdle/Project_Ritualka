import sqlite3

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import fetch_all_products, fetch_product_by_id, get_db

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_data(request: Request):
    return templates.TemplateResponse("glavnaya.html", {"request": request})

@router.get("/category/{name}")             
async def category(name: str):
    return f"Категория: {name}"


@router.get("/products")
async def list_products(
    db: sqlite3.Connection = Depends(get_db),
):
    products = fetch_all_products(db)
    return {"items": products}


@router.get("/product/{product_id}")
async def product(
    product_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    product_row = fetch_product_by_id(db, product_id)
    if product_row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product_row)

@router.get("/info", response_class=HTMLResponse)
async def company(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})