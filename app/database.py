import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Mapping, Optional, Union

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATABASE_PATH = DATA_DIR / "database.db"

def _list_product_columns(connection: sqlite3.Connection) -> List[str]:
    """Return the current column names for the ``products`` table."""

    cursor = connection.execute("PRAGMA table_info(products)")
    return [row[1] for row in cursor.fetchall()]


def _ensure_schema(connection: sqlite3.Connection) -> None:
    """Create missing tables or columns required by the application."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            img_path TEXT,
            category TEXT DEFAULT 'general'
        )
        """
    )

    existing_columns = set(_list_product_columns(connection))

    schema_updated = False

    if "img_path" not in existing_columns:
        if "image_path" in existing_columns:
            try:
                connection.execute(
                    "ALTER TABLE products RENAME COLUMN image_path TO img_path"
                )
            except sqlite3.OperationalError:
                connection.execute("ALTER TABLE products ADD COLUMN img_path TEXT")
                connection.execute(
                    """
                    UPDATE products
                    SET img_path = image_path
                    WHERE image_path IS NOT NULL AND TRIM(image_path) != ''
                    """
                )
        else:
            connection.execute("ALTER TABLE products ADD COLUMN img_path TEXT")
        schema_updated = True

    if "image_url" in existing_columns:
        connection.execute(
            """
            UPDATE products
            SET img_path = image_url
            WHERE (img_path IS NULL OR TRIM(img_path) = '')
              AND image_url IS NOT NULL AND TRIM(image_url) != ''
            """
        )
        schema_updated = True

    if "category" not in existing_columns:
        connection.execute(
            "ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'general'"
        )
        schema_updated = True
        connection.execute(
            """
            UPDATE products
            SET category = 'general'
            WHERE category IS NULL OR TRIM(category) = ''
            """
        )

    if schema_updated:
        connection.commit()


def _image_column(connection: sqlite3.Connection) -> str:
    """Return the column storing image paths, ensuring it exists."""

    columns = set(_list_product_columns(connection))
    if "img_path" in columns:
        return "img_path"
    if "image_path" in columns:
        return "image_path"

    connection.execute("ALTER TABLE products ADD COLUMN img_path TEXT")
    connection.commit()
    return "img_path"


def _image_select_clause(connection: sqlite3.Connection) -> str:
    """Return a SQL fragment that aliases the image column to ``img_path``."""

    column = _image_column(connection)
    if column == "img_path":
        return "img_path"
    return f"{column} AS img_path"



@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    _ensure_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    with get_connection() as connection:
        yield connection

@dataclass(init=False)
class ProductData:
    name: str
    price: float
    description: Optional[str] = None
    img_path: Optional[str] = None
    category: Optional[str] = None
    image_path: Optional[str] = field(
        default=None, repr=False, compare=False, init=False
    )

    def __init__(
        self,
        name: str,
        price: float,
        description: Optional[str] = None,
        img_path: Optional[str] = None,
        category: Optional[str] = None,
        *,
        image_path: Optional[str] = None,
    ) -> None:
        self.name = name
        self.price = price
        self.description = description
        resolved_image = img_path if img_path is not None else image_path
        self.img_path = resolved_image
        self.image_path = resolved_image
        self.category = category

ProductInput = Union[ProductData, Mapping[str, Any]]

##         Функции для взаимодестввия 

def fetch_all_products(db: sqlite3.Connection) -> List[Dict[str, object]]:
    """Return all products ordered by their identifier."""

    image_clause = _image_select_clause(db)
    cursor = db.execute(
        f"SELECT id, name, price, description, {image_clause}, category FROM products ORDER BY id"
    )
    return [dict(row) for row in cursor.fetchall()]


def fetch_product_by_id(
    db: sqlite3.Connection, product_id: int
) -> Optional[Dict[str, object]]:
    """Return a product by identifier if it exists."""

    image_clause = _image_select_clause(db)
    cursor = db.execute(
        f"""
        SELECT id, name, price, description, {image_clause}, category
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)

def _get_field(data: ProductInput, field: str, default: Any = None) -> Any:
    """Return ``field`` from ``data`` whether it's an object or mapping."""

    if isinstance(data, Mapping) and field in data:
        return data[field]
    return getattr(data, field, default)


def _extract_image_value(data: ProductData) -> Optional[str]:
    """Return the image path stored on ``data``.

    The helper tolerates older ``ProductData`` instances that may still expose
    an ``image_path`` attribute to avoid attribute errors while the
    application is running with mixed code versions.
    """

    if hasattr(data, "img_path"):
        return getattr(data, "img_path")
    return getattr(data, "image_path", None)



def create_product(db: sqlite3.Connection, data: ProductData) -> int:
    """Insert a new product and return its identifier."""

    image_column = _image_column(db)
    image_value = _extract_image_value(data)
    cursor = db.execute(
        f"""
        INSERT INTO products (name, price, description, {image_column}, category)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            _get_field(data, "name"),
            _get_field(data, "price"),
            _get_field(data, "description"),
            image_value,
            _get_field(data, "category") or "general",
        ),
    )
    db.commit()
    return int(cursor.lastrowid)


def update_product(
    db: sqlite3.Connection, product_id: int, data: ProductData
) -> bool:
    """Update an existing product. Returns True when a row was updated."""

    image_column = _image_column(db)
    image_value = _extract_image_value(data)
    cursor = db.execute(
        f"""
        UPDATE products
        SET name = ?, price = ?, description = ?, {image_column} = ?, category = ?
        WHERE id = ?
        """,
        (
            _get_field(data, "name"),
            _get_field(data, "price"),
            _get_field(data, "description"),
            image_value,
            _get_field(data, "category") or "general",
            product_id,
        ),
    )
    db.commit()
    return cursor.rowcount > 0


def delete_product(db: sqlite3.Connection, product_id: int) -> bool:
    """Delete a product by identifier. Returns True when a row was removed."""

    cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return cursor.rowcount > 0