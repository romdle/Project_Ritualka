import sqlite3

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import fetch_all_products, fetch_product_by_id, get_db

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()

def _render_spa(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("glavnaya.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return _render_spa(request)


@router.get("/catalog", response_class=HTMLResponse)
async def catalog_page(request: Request) -> HTMLResponse:
    return _render_spa(request)


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request) -> HTMLResponse:
    return _render_spa(request)


@router.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request) -> HTMLResponse:
    return _render_spa(request)


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(request: Request, product_id: int) -> HTMLResponse:  # noqa: ARG001
    return _render_spa(request)


@router.get("/api/products")
async def list_products(
    db: sqlite3.Connection = Depends(get_db),
):
    products = fetch_all_products(db)
    return {"items": products}


@router.get("/api/products/{product_id}")
async def get_product(
    product_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    product_row = fetch_product_by_id(db, product_id)
    if product_row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product_row)
