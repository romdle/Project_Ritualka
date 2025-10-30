import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import get_db

templates = Jinja2Templates(directory="templates")
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
    cursor = db.execute(
        "SELECT name, price, description, image_url FROM products ORDER BY id"
    )
    products = [dict(row) for row in cursor.fetchall()]
    return {"items": products}


@router.get("/product/{product_id}")
async def product(
    product_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    cursor = db.execute(
        "SELECT name, price, description, image_url FROM products WHERE id = ?",
        (product_id,),
    )
    product_row = cursor.fetchone()
    if product_row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product_row)

@router.get("/info", response_class=HTMLResponse)
async def company(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})