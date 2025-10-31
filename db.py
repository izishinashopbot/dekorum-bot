# db.py
import os
import sqlite3
import time
from contextlib import closing

DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init():
    with closing(_conn()) as c:
        cur = c.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              status TEXT NOT NULL DEFAULT 'created',
              created_at INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
              order_id INTEGER PRIMARY KEY,
              user_id INTEGER NOT NULL
            )
        """)
        c.commit()

_init()

# ------- API, які використовує bot.py -------

def create_order(user_id: int) -> int:
    """Створює замовлення і повертає order_id."""
    with closing(_conn()) as c:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO orders(user_id, status, created_at) VALUES (?, 'created', ?)",
            (user_id, int(time.time()))
        )
        c.commit()
        return cur.lastrowid

def get_order(order_id: int) -> dict | None:
    with closing(_conn()) as c:
        cur = c.cursor()
        cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def set_order_status(order_id: int, status: str) -> None:
    with closing(_conn()) as c:
        c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        c.commit()

def save_join_request(order_id: int, user_id: int) -> None:
    """Запам’ятати, що цей користувач чекає доступ після оплати."""
    with closing(_conn()) as c:
        c.execute(
            "INSERT OR REPLACE INTO join_requests(order_id, user_id) VALUES (?, ?)",
            (order_id, user_id)
        )
        c.commit()

def pop_join_request(order_id: int) -> int | None:
    """Повертає user_id і видаляє запис про очікування доступу."""
    with closing(_conn()) as c:
        cur = c.cursor()
        cur.execute("SELECT user_id FROM join_requests WHERE order_id = ?", (order_id,))
        row = cur.fetchone()
        if not row:
            return None
        user_id = row["user_id"]
        cur.execute("DELETE FROM join_requests WHERE order_id = ?", (order_id,))
        c.commit()
        return user_id
