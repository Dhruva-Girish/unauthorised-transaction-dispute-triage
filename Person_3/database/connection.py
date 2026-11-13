"""
connection.py — SQLite Database Connection Provider
Configures WAL (Write-Ahead Logging) mode and thread-safe connections.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "database" / "disputes.db"
SCHEMA_FILE = ROOT / "database" / "schema.sql"


def get_db_connection() -> sqlite3.Connection:
    """Return a connection with WAL mode enabled and Row factory."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    """Execute initial schema migration."""
    with get_db_connection() as conn:
        if SCHEMA_FILE.exists():
            conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.commit()


# Auto-init on import
init_db()
