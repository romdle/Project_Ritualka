from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional, Union
from uuid import uuid4
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.datastructures import UploadFile as StarletteUploadFile

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

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_ROOT = STATIC_DIR.resolve()
UPLOAD_DIR = STATIC_DIR / "uploads"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

CATEGORY_CHOICES = [
    "Стандартный",
    "Эксклюзивный",
    "Семейный",
    "Детский",
]

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_product_form(
    name: str,
    price: str,
    description: Optional[str],
    category: Optional[str],
    image_path: Optional[str],
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

    category_value = category.strip() if category else None
    if not category_value:
        return None
    
    if category_value not in CATEGORY_CHOICES:
        return None

    return ProductData(
        name=name,
        price=price_value,
        description=description_value or None,
        img_path=image_path or None,
        category=category_value,
    )


def _prepare_category_choices(selected: Optional[str]) -> tuple[list[str], str]:
    value = selected.strip() if isinstance(selected, str) else ""
    choices = list(CATEGORY_CHOICES)
    if value and value not in choices:
        choices.append(value)

    if not value and choices:
        value = choices[0]

    return choices, value

UploadFileType = Union[UploadFile, StarletteUploadFile]


async def _save_uploaded_image(upload: UploadFileType) -> str:
    filename = Path(upload.filename or "")
    suffix = filename.suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Недопустимый формат изображения.")

    stem = filename.stem or "image"
    unique_name = f"{stem}_{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / unique_name

    data = await upload.read()
    with destination.open("wb") as buffer:
        buffer.write(data)
    await upload.close()

    return destination.relative_to(STATIC_DIR).as_posix()


def _image_storage_path(image_reference: str) -> Optional[Path]:
    if not image_reference:
        return None

    relative = Path(str(image_reference).strip().lstrip("/"))
    try:
        candidate = (STATIC_ROOT / relative).resolve()
        candidate.relative_to(STATIC_ROOT)
    except (ValueError, RuntimeError):
        return None

    return candidate


def _delete_image_file(image_reference: str) -> None:
    path = _image_storage_path(image_reference)
    if path and path.exists():
        try:
            path.unlink()
        except OSError:
            pass


async def _resolve_image_path(
    upload: Optional[UploadFile], existing_image: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    existing_value_raw = (
        existing_image.strip() if isinstance(existing_image, str) else ""
    )
    existing_value = existing_value_raw
    if existing_value:
        resolved_existing = _image_storage_path(existing_value)
        if resolved_existing:
            existing_value = resolved_existing.relative_to(STATIC_ROOT).as_posix()

    if isinstance(upload, (UploadFile, StarletteUploadFile)):
        filename = upload.filename or ""
        if filename:
            try:
                saved_path = await _save_uploaded_image(upload)
            except ValueError:
                await upload.close()
                raise

            if existing_value and existing_value != saved_path:
                return saved_path, existing_value
            return saved_path, None
        
        await upload.close()

    if existing_value:
        return existing_value, None

    return None, None


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
    categories, selected_category = _prepare_category_choices(None)
    context: Dict[str, object] = {
        "request": request,
        "action": "/admin/products/new",
        "title": "Добавить продукт",
        "submit_label": "Добавить",
        "product": None,
        "categories": categories,
        "selected_category": selected_category,
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

    form = await request.form()
    name = str(form.get("name", ""))
    price = str(form.get("price", ""))
    description = form.get("description")
    category = str(form.get("category", ""))
    upload = form.get("image")
    existing_image_raw = form.get("existing_image")
    existing_image = (
        existing_image_raw.strip()
        if isinstance(existing_image_raw, str)
        else ""
    )

    try:
        image_path, old_image_to_delete = await _resolve_image_path(
            upload, existing_image
        )
    except ValueError as exc:
        categories, selected_category = _prepare_category_choices(category)
        context = {
            "request": request,
            "action": "/admin/products/new",
            "title": "Добавить продукт",
            "submit_label": "Добавить",
            "product": {
                "name": name,
                "price": price,
                "description": description,
                "category": category,
                "img_path": existing_image,
                "image_path": existing_image,
            },
            "categories": categories,
            "selected_category": selected_category,
            "error": str(exc),
        }
        return templates.TemplateResponse(
            "admin/product_form.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    product_data = _parse_product_form(name, price, description, category, image_path)
    if product_data is None:
        categories, selected_category = _prepare_category_choices(category)
        context = {
            "request": request,
            "action": "/admin/products/new",
            "title": "Добавить продукт",
            "submit_label": "Добавить",
            "product": {
                "name": name,
                "price": price,
                "description": description,
                "category": category,
                "img_path": image_path,
                "image_path": image_path,
            },
            "categories": categories,
            "selected_category": selected_category,
            "error": "Пожалуйста, укажите корректные данные продукта.",
        }
        return templates.TemplateResponse(
            "admin/product_form.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    create_product(db, product_data)
    if old_image_to_delete:
        _delete_image_file(old_image_to_delete)
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
    
    selected_category = None
    if isinstance(product, dict):
        selected_category = product.get("category")
    else:
        selected_category = getattr(product, "category", None)
    categories, selected_category = _prepare_category_choices(selected_category)
    context = {
        "request": request,
        "action": f"/admin/products/{product_id}",
        "title": "Редактирование продукта",
        "submit_label": "Сохранить",
        "product": product,
        "categories": categories,
        "selected_category": selected_category,
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

    form = await request.form()
    name = str(form.get("name", ""))
    price = str(form.get("price", ""))
    description = form.get("description")
    category = str(form.get("category", ""))
    upload = form.get("image")
    existing_image_raw = form.get("existing_image")
    existing_image = (
        existing_image_raw.strip()
        if isinstance(existing_image_raw, str)
        else ""
    )

    existing = fetch_product_by_id(db, product_id)
    if existing is None:
        return templates.TemplateResponse(
            "admin/not_found.html",
            {"request": request, "product_id": product_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    categories_for_render, selected_category_value = _prepare_category_choices(category)
    current_image: Optional[str] = None
    if isinstance(existing, dict):
        current_image = existing.get("img_path") or existing.get("image_path")
    else:
        current_image = getattr(existing, "img_path", None) or getattr(
            existing, "image_path", None
        )

    old_image_to_delete: Optional[str] = None
    try:
        image_path, old_image_to_delete = await _resolve_image_path(
            upload, existing_image or current_image
        )
    except ValueError as exc:
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
                "category": category,
                "img_path": existing_image or current_image,
                "image_path": existing_image or current_image,
            },
            "categories": categories_for_render,
            "selected_category": selected_category_value,
            "error": str(exc),
        }
        return templates.TemplateResponse(
            "admin/product_form.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    product_data = _parse_product_form(name, price, description, category, image_path)
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
                "category": category,
                "img_path": image_path,
                "image_path": image_path,
            },
            "categories": categories_for_render,
            "selected_category": selected_category_value,
            "error": "Пожалуйста, укажите корректные данные продукта.",
        }
        return templates.TemplateResponse(
            "admin/product_form.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    updated = update_product(db, product_id, product_data)
    if updated and old_image_to_delete:
        _delete_image_file(old_image_to_delete)
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

    image_reference: Optional[str] = None
    if isinstance(product, dict):
        image_reference = (
            product.get("img_path")
            or product.get("image_path")
            or product.get("image")
        )
    else:
        image_reference = (
            getattr(product, "img_path", None)
            or getattr(product, "image_path", None)
            or getattr(product, "image", None)
        )

    deleted = delete_product(db, product_id)
    if deleted and image_reference:
        _delete_image_file(image_reference)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
