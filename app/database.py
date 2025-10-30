import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATABASE_PATH = DATA_DIR / "database.db"

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
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
    image_url: Optional[str] = None



##         Функции для взаимодестввия 

def fetch_all_products(db: sqlite3.Connection) -> List[Dict[str, object]]:
    """Return all products ordered by their identifier."""

    cursor = db.execute(
        "SELECT id, name, price, description, image_url FROM products ORDER BY id"
    )
    return [dict(row) for row in cursor.fetchall()]


def fetch_product_by_id(
    db: sqlite3.Connection, product_id: int
) -> Optional[Dict[str, object]]:
    """Return a product by identifier if it exists."""

    cursor = db.execute(
        "SELECT id, name, price, description, image_url FROM products WHERE id = ?",
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
        INSERT INTO products (name, price, description, image_url)
        VALUES (?, ?, ?, ?)
        """,
        (data.name, data.price, data.description, data.image_url),
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
        SET name = ?, price = ?, description = ?, image_url = ?
        WHERE id = ?
        """,
        (data.name, data.price, data.description, data.image_url, product_id),
    )
    db.commit()
    return cursor.rowcount > 0


def delete_product(db: sqlite3.Connection, product_id: int) -> bool:
    """Delete a product by identifier. Returns True when a row was removed."""

    cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return cursor.rowcount > 0