"""Routes powering the admin panel."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import auth
from database import (
    ProductData,
    create_product,
    delete_product,
    fetch_all_products,
    fetch_product_by_id,
    update_product,
    get_db,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_product_form(
    name: str,
    price: str,
    description: Optional[str],
    image_url: Optional[str],
) -> Optional[ProductData]:
    """Validate and transform raw form data into ``ProductData``."""

    name = name.strip()
    if not name:
        return None

    try:
        price_value = float(price)
    except (TypeError, ValueError):
        return None

    description_value = description.strip() if description else None
    image_url_value = image_url.strip() if image_url else None

    return ProductData(
        name=name,
        price=price_value,
        description=description_value or None,
        image_url=image_url_value or None,
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Render the administrator login page."""

    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": None}
    )


async def _read_form_data(request: Request) -> Dict[str, str]:
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    encoding = "utf-8"
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("charset="):
            candidate = part.split("=", 1)[1].strip()
            if candidate:
                encoding = candidate.lower()
            break

    try:
        text = body.decode(encoding)
    except LookupError:
        text = body.decode("utf-8", errors="ignore")

    parsed = parse_qs(text, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


@router.post("/login")
async def login(request: Request) -> Response:
    """Authenticate the administrator and redirect to the dashboard."""

    form_data = await _read_form_data(request)
    username = form_data.get("username", "")
    password = form_data.get("password", "")

    if auth.verify_credentials(username, password):
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        auth.login_user(response)
        return response

    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": "Неверный логин или пароль."},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@router.get("/logout")
async def logout() -> RedirectResponse:
    """Terminate the current administrator session."""

    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    auth.logout_user(response)
    return response


@router.get("/", response_class=HTMLResponse, dependencies=[Depends(auth.require_login)])
async def dashboard(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    """List all products in the database."""

    products = fetch_all_products(db)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "products": products},
    )


@router.get(
    "/products/new",
    response_class=HTMLResponse,
    dependencies=[Depends(auth.require_login)],
)
async def new_product_form(request: Request) -> HTMLResponse:
    """Render the form used to add a new product."""

    context: Dict[str, object] = {
        "request": request,
        "action": "/admin/products/new",
        "title": "Добавить продукт",
        "submit_label": "Добавить",
        "product": None,
        "error": None,
    }
    return templates.TemplateResponse("admin/product_form.html", context)


@router.post(
    "/products/new",
    dependencies=[Depends(auth.require_login)],
)
async def create_product_action(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    """Persist a new product in the database."""

    form_data = await _read_form_data(request)
    name = form_data.get("name", "")
    price = form_data.get("price", "")
    description = form_data.get("description")
    image_url = form_data.get("image_url")

    product_data = _parse_product_form(name, price, description, image_url)
    if product_data is None:
        context = {
            "request": request,
            "action": "/admin/products/new",
            "title": "Добавить продукт",
            "submit_label": "Добавить",
            "product": {"name": name, "price": price, "description": description, "image_url": image_url},
            "error": "Пожалуйста, укажите корректные данные продукта.",
        }
        return templates.TemplateResponse(
            "admin/product_form.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    create_product(db, product_data)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.get(
    "/products/{product_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(auth.require_login)],
)
async def edit_product_form(
    product_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    """Render the form for viewing and editing an existing product."""

    product = fetch_product_by_id(db, product_id)
    if product is None:
        return templates.TemplateResponse(
            "admin/not_found.html",
            {"request": request, "product_id": product_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    context = {
        "request": request,
        "action": f"/admin/products/{product_id}",
        "title": "Редактирование продукта",
        "submit_label": "Сохранить",
        "product": product,
        "error": None,
    }
    return templates.TemplateResponse("admin/product_form.html", context)


@router.post(
    "/products/{product_id}",
    dependencies=[Depends(auth.require_login)],
)
async def update_product_action(
    product_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    """Update an existing product."""

    form_data = await _read_form_data(request)
    name = form_data.get("name", "")
    price = form_data.get("price", "")
    description = form_data.get("description")
    image_url = form_data.get("image_url")

    existing = fetch_product_by_id(db, product_id)
    if existing is None:
        return templates.TemplateResponse(
            "admin/not_found.html",
            {"request": request, "product_id": product_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    product_data = _parse_product_form(name, price, description, image_url)
    if product_data is None:
        context = {
            "request": request,
            "action": f"/admin/products/{product_id}",
            "title": "Редактирование продукта",
            "submit_label": "Сохранить",
            "product": {
                "id": product_id,
                "name": name,
                "price": price,
                "description": description,
                "image_url": image_url,
            },
            "error": "Пожалуйста, укажите корректные данные продукта.",
        }
        return templates.TemplateResponse(
            "admin/product_form.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    update_product(db, product_id, product_data)
    return RedirectResponse(url=f"/admin/products/{product_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get(
    "/products/{product_id}/delete",
    response_class=HTMLResponse,
    dependencies=[Depends(auth.require_login)],
)
async def delete_product_form(
    product_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    """Render a confirmation page for product deletion."""

    product = fetch_product_by_id(db, product_id)
    if product is None:
        return templates.TemplateResponse(
            "admin/not_found.html",
            {"request": request, "product_id": product_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "admin/delete_product.html",
        {"request": request, "product": product},
    )


@router.post(
    "/products/{product_id}/delete",
    dependencies=[Depends(auth.require_login)],
)
async def delete_product_action(
    product_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    """Remove the product from the database."""

    product = fetch_product_by_id(db, product_id)
    if product is None:
        return templates.TemplateResponse(
            "admin/not_found.html",
            {"request": request, "product_id": product_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    delete_product(db, product_id)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
