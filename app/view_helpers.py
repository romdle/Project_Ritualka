"""Utility helpers for preparing data for HTML templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import math
import re


CATEGORY_TITLES = {
    "Стандартный": "Стандартные памятники",
    "Семейный": "Семейные памятники",
    "Эксклюзивный": "Эксклюзивные памятники",
    "Детский": "Детские памятники",
}

CATEGORY_ORDER: Sequence[str] = (
    "Стандартный",
    "Семейный",
    "Эксклюзивный",
    "Детский",
)

CATEGORY_PRESETS: Sequence[dict[str, Sequence[str]]] = (
    {
        "slug": "standartnye",
        "label": "Стандартные",
        "names": ("Стандартный", "Стандартные памятники"),
    },
    {
        "slug": "semeinye",
        "label": "Семейные",
        "names": ("Семейный", "Семейные памятники"),
    },
    {
        "slug": "eksklyuzivnye",
        "label": "Эксклюзивные",
        "names": ("Эксклюзивный", "Эксклюзивные памятники"),
    },
    {
        "slug": "detskie",
        "label": "Детские",
        "names": ("Детский", "Детские памятники"),
    },
)

CATEGORY_PRESET_INDEX = {
    preset["slug"]: index for index, preset in enumerate(CATEGORY_PRESETS)
}


PRICE_REQUEST_TEXT = "по запросу"


_slug_invalid_re = re.compile(r"[^\w\d]+", re.IGNORECASE)
_http_re = re.compile(r"^https?://", re.IGNORECASE)


def resolve_image_path(value: Optional[str]) -> str:
    """Return a web accessible path for ``value``."""

    if not value:
        return ""

    raw = str(value).strip()
    if not raw:
        return ""

    if _http_re.match(raw):
        return raw

    if raw.startswith("/"):
        return raw

    normalized = raw.lstrip("./")
    if normalized.startswith("static/"):
        return "/" + normalized.lstrip("/")

    return "/static/" + normalized.lstrip("/")


def display_category_name(value: Optional[str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return "Без категории"
    return CATEGORY_TITLES.get(raw, raw)


def _category_preset_by_name(name: Optional[str]) -> Optional[dict[str, Sequence[str]]]:
    if not name:
        return None
    normalized = name.strip().lower()
    for preset in CATEGORY_PRESETS:
        if any(candidate.lower() == normalized for candidate in preset["names"]):
            return preset
    return None


def _category_preset_by_slug(slug: Optional[str]) -> Optional[dict[str, Sequence[str]]]:
    if not slug:
        return None
    normalized = slug.strip().lower()
    for preset in CATEGORY_PRESETS:
        if preset["slug"] == normalized:
            return preset
    return None


def category_slug(value: Optional[str]) -> str:
    preset = _category_preset_by_name(value)
    if preset:
        return preset["slug"]

    label = display_category_name(value)
    normalized = _slug_invalid_re.sub("-", label.strip().lower())
    normalized = normalized.strip("-")
    return normalized or "uncategorized"


def category_label(value: Optional[str]) -> str:
    preset = _category_preset_by_name(value)
    if preset:
        return preset["label"]
    return display_category_name(value)


def parse_numeric_price(value: Optional[object]) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    if PRICE_REQUEST_TEXT in text.lower():
        return None

    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return None

    try:
        return float(digits)
    except ValueError:
        return None


def format_number(value: float) -> str:
    return format(value, ",.0f").replace(",", " ")


def price_display(value: Optional[object]) -> dict[str, str]:
    numeric = parse_numeric_price(value)
    if numeric is not None:
        amount = f"{format_number(numeric)} ₽"
        return {"prefix": "от", "text": amount}

    text = (str(value).strip() if value is not None else "")
    if text and text.lower() != PRICE_REQUEST_TEXT:
        return {"prefix": "от", "text": text}

    return {"prefix": "", "text": PRICE_REQUEST_TEXT}


def format_description(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.replace("\r\n", "\n").replace("\n", "<br>")


@dataclass
class ProductView:
    id: int
    name: str
    price: Optional[object]
    description: str
    category: Optional[str]
    img_path: Optional[str]

    @property
    def numeric_price(self) -> Optional[float]:
        return parse_numeric_price(self.price)

    @property
    def price_display(self) -> dict[str, str]:
        return price_display(self.price)

    @property
    def price_text(self) -> str:
        parts = self.price_display
        if parts["prefix"]:
            return f"{parts['prefix']} {parts['text']}"
        return parts["text"]

    @property
    def image_url(self) -> str:
        return resolve_image_path(self.img_path)

    @property
    def category_name(self) -> str:
        return display_category_name(self.category)

    @property
    def category_slug(self) -> str:
        return category_slug(self.category)

    @property
    def link(self) -> str:
        return f"/product/{self.id}"


def build_product_views(rows: Iterable[dict[str, object]]) -> List[ProductView]:
    products: List[ProductView] = []
    for row in rows:
        products.append(
            ProductView(
                id=int(row.get("id")),
                name=str(row.get("name") or row.get("title") or ""),
                price=row.get("price"),
                description=str(row.get("description") or ""),
                category=row.get("category"),
                img_path=row.get("img_path") or row.get("image_path"),
            )
        )
    return products


def ordered_categories(products: Sequence[ProductView]) -> List[dict[str, object]]:
    groups: dict[str, List[ProductView]] = {}
    for product in products:
        key = (product.category or "").strip() or "Без категории"
        groups.setdefault(key, []).append(product)

    def category_order_key(name: str) -> tuple[int, str]:
        try:
            idx = CATEGORY_ORDER.index(name)
        except ValueError:
            idx = len(CATEGORY_ORDER)
        return (idx, display_category_name(name))

    entries: List[tuple[str, List[ProductView]]] = list(groups.items())
    entries.sort(key=lambda item: category_order_key(item[0]))

    result: List[dict[str, object]] = []
    for key, items in entries:
        result.append(
            {
                "key": key,
                "display": display_category_name(key),
                "slug": category_slug(key),
                "items": items,
            }
        )
    return result


def catalog_price_bounds(products: Sequence[ProductView]) -> dict[str, int]:
    minimum = math.inf
    maximum = 0
    for product in products:
        value = product.numeric_price
        if value is None:
            continue
        minimum = min(minimum, value)
        maximum = max(maximum, value)

    if minimum is math.inf or maximum <= 0:
        return {"min": 0, "max": 0}

    return {"min": int(minimum), "max": int(maximum)}


def catalog_categories(products: Sequence[ProductView]) -> List[dict[str, object]]:
    totals: dict[str, List[ProductView]] = {}
    for product in products:
        slug = product.category_slug
        totals.setdefault(slug, []).append(product)

    result = [
        {
            "slug": "all",
            "label": "Все памятники",
            "count": len(products),
        }
    ]

    used: set[str] = set()

    for preset in CATEGORY_PRESETS:
        slug = preset["slug"]
        items = totals.get(slug, [])
        result.append(
            {
                "slug": slug,
                "label": preset["label"],
                "count": len(items),
            }
        )
        used.add(slug)

    def sort_key(item: tuple[str, List[ProductView]]) -> tuple[int, str]:
        slug, items = item
        preset = _category_preset_by_slug(slug)
        if preset:
            return (CATEGORY_PRESETS.index(preset), preset["label"])
        first = items[0] if items else None
        try:
            fallback = CATEGORY_ORDER.index(first.category if first else "")
        except ValueError:
            fallback = len(CATEGORY_ORDER)
        return (fallback, category_label(first.category if first else ""))

    remaining = [(slug, items) for slug, items in totals.items() if slug not in used]

    for slug, items in sorted(remaining, key=sort_key):
        result.append(
            {
                "slug": slug,
                "label": category_label(items[0].category if items else ""),
                "count": len(items),
            }
        )

    return result


def apply_catalog_filters(
    products: Sequence[ProductView],
    *,
    category: str,
    sort: str,
    price_from: Optional[int],
    price_to: Optional[int],
) -> List[ProductView]:
    filtered: List[ProductView] = []
    price_active = (
        price_from is not None
        and price_to is not None
        and price_to > price_from
    )

    for product in products:
        if category != "all" and product.category_slug != category:
            continue
        if price_active:
            value = product.numeric_price
            if value is None:
                continue
            if value < price_from or value > price_to:
                continue
        filtered.append(product)

    def sort_key_price(item: ProductView) -> tuple[int, str]:
        value = item.numeric_price
        if value is None:
            return (math.inf, item.name.lower())
        return (int(value), item.name.lower())

    def sort_key_name(item: ProductView) -> str:
        return item.name.lower()

    def sort_key_category(item: ProductView) -> tuple[str, str]:
        return (item.category_name.lower(), item.name.lower())

    if sort == "price-desc":
        filtered.sort(key=sort_key_price)
        filtered.reverse()
    elif sort == "category":
        filtered.sort(key=sort_key_category)
    elif sort == "name":
        filtered.sort(key=sort_key_name)
    else:
        filtered.sort(key=sort_key_price)

    return filtered


def similar_products(
    product: ProductView, products: Sequence[ProductView]
) -> List[ProductView]:
    same_category = [
        item
        for item in products
        if item.id != product.id
        and item.category_slug == product.category_slug
    ]
    if same_category:
        return same_category

    standard = [
        item
        for item in products
        if item.id != product.id and item.category_slug == category_slug("Стандартный")
    ]
    if standard:
        return standard

    return [item for item in products if item.id != product.id]


CATALOG_SORT_OPTIONS = (
    {"value": "price-asc", "label": "По цене ↑", "icon": "arrow-up"},
    {"value": "price-desc", "label": "По цене ↓", "icon": "arrow-down"},
    {"value": "category", "label": "По категории", "icon": "grid"},
    {"value": "name", "label": "По названию", "icon": "letters"},
)


def clamp_price(value: Optional[int], *, bounds: dict[str, int]) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None

    minimum = bounds.get("min", 0)
    maximum = bounds.get("max", 0)

    if maximum <= minimum:
        return None

    return max(minimum, min(maximum, parsed))


def slider_step(bounds: dict[str, int]) -> int:
    minimum = bounds.get("min", 0)
    maximum = bounds.get("max", 0)
    span = max(1, maximum - minimum)
    if span <= 10_000:
        return 1_000
    if span <= 50_000:
        return 5_000
    if span <= 200_000:
        return 10_000
    return 20_000
