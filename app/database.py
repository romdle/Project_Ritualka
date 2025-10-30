import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATABASE_PATH = DATA_DIR / "database.db"

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

    cursor = connection.execute("PRAGMA table_info(products)")
    existing_columns = {row[1] for row in cursor.fetchall()}

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

@dataclass
class ProductData:
    name: str
    price: float
    description: Optional[str] = None
    image_path: Optional[str] = None
    category: Optional[str] = None



##         Функции для взаимодестввия 

def fetch_all_products(db: sqlite3.Connection) -> List[Dict[str, object]]:
    """Return all products ordered by their identifier."""

    cursor = db.execute(
        "SELECT id, name, price, description, image_path, category FROM products ORDER BY id"
    )
    return [dict(row) for row in cursor.fetchall()]


def fetch_product_by_id(
    db: sqlite3.Connection, product_id: int
) -> Optional[Dict[str, object]]:
    """Return a product by identifier if it exists."""

    cursor = db.execute(
        """
        SELECT id, name, price, description, image_path, category
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)


def create_product(db: sqlite3.Connection, data: ProductData) -> int:
    """Insert a new product and return its identifier."""

    cursor = db.execute(
        """
        INSERT INTO products (name, price, description, image_path, category)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.name,
            data.price,
            data.description,
            data.image_path,
            data.category or "general",
        ),
    )
    db.commit()
    return int(cursor.lastrowid)


def update_product(
    db: sqlite3.Connection, product_id: int, data: ProductData
) -> bool:
    """Update an existing product. Returns True when a row was updated."""

    cursor = db.execute(
        """
        UPDATE products
        SET name = ?, price = ?, description = ?, image_path = ?, category = ?
        WHERE id = ?
        """,
        (
            data.name,
            data.price,
            data.description,
            data.image_path,
            data.category or "general",
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