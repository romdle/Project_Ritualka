from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import fetch_all_products, fetch_product_by_id, get_db
from view_helpers import (
    CATALOG_SORT_OPTIONS,
    apply_catalog_filters,
    build_product_views,
    catalog_categories,
    catalog_price_bounds,
    clamp_price,
    ordered_categories,
    similar_products,
    slider_step,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _format_number_ru(value: object) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "0"
    return format(number, ",").replace(",", " ")


templates.env.filters["format_number_ru"] = _format_number_ru

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    products_raw = fetch_all_products(db)
    products = build_product_views(products_raw)
    categories = ordered_categories(products)
    context = {
        "request": request,
        "active_page": "home",
        "category_groups": categories,
    }
    return templates.TemplateResponse("home.html", context)


@router.get("/catalog", response_class=HTMLResponse)
async def catalog_page(
    request: Request,
    category: str = Query("all"),
    sort: str = Query("price-asc"),
    price_from: Optional[int] = Query(None, alias="price_from"),
    price_to: Optional[int] = Query(None, alias="price_to"),
    db: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    products_raw = fetch_all_products(db)
    products = build_product_views(products_raw)
    bounds = catalog_price_bounds(products)

    category_slug = category.strip().lower() if category else "all"
    sort_value = sort.strip().lower() if sort else "price-asc"
    allowed_sorts = {option["value"] for option in CATALOG_SORT_OPTIONS}
    if sort_value not in allowed_sorts:
        sort_value = "price-asc"

    price_min = bounds.get("min", 0)
    price_max = bounds.get("max", 0)
    clamped_from = clamp_price(price_from, bounds=bounds)
    clamped_to = clamp_price(price_to, bounds=bounds)

    if clamped_from is None:
        clamped_from = price_min
    if clamped_to is None:
        clamped_to = price_max
    if price_max and clamped_from > clamped_to:
        clamped_from, clamped_to = clamped_to, clamped_from

    filtered = apply_catalog_filters(
        products,
        category=category_slug or "all",
        sort=sort_value,
        price_from=clamped_from,
        price_to=clamped_to,
    )

    categories = catalog_categories(products)

    context = {
        "request": request,
        "active_page": "catalog",
        "categories": categories,
        "products": filtered,
        "filters": {
            "category": category_slug or "all",
            "sort": sort_value,
            "price_from": clamped_from,
            "price_to": clamped_to,
            "price_min": price_min,
            "price_max": price_max,
        },
        "sort_options": CATALOG_SORT_OPTIONS,
        "slider_step": slider_step(bounds),
    }
    return templates.TemplateResponse("catalog.html", context)


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "about.html", {"request": request, "active_page": "about"}
    )


@router.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "contacts.html", {"request": request, "active_page": "contacts"}
    )


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(
    request: Request,
    product_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    product_row = fetch_product_by_id(db, product_id)
    if product_row is None:
        raise HTTPException(status_code=404, detail="Product not found")

    all_products = build_product_views(fetch_all_products(db))
    product_view = build_product_views([product_row])[0]
    similar = similar_products(product_view, all_products)

    context = {
        "request": request,
        "active_page": "catalog",
        "product": product_view,
        "similar_items": similar,
    }
    return templates.TemplateResponse("product.html", context)


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
