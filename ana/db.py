import sqlite3
import os
from typing import Optional

DB_PATH = os.path.join(os.path.expanduser("~"), ".ana", "events.db")


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            day      INTEGER NOT NULL,
            month    INTEGER NOT NULL,
            year     INTEGER NOT NULL,
            time     TEXT,
            text     TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn
