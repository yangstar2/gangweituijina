"""SQLite3 schema stubs for users / members / sessions / outlines."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    openid TEXT UNIQUE NOT NULL,
    nickname TEXT,
    avatar_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'free',
    expires_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,          -- courseware | exam
    title TEXT,
    status TEXT NOT NULL DEFAULT 'clarifying',  -- clarifying | outlined | previewing | done
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,                  -- user | teacher | system
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS outlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL UNIQUE,
    key_points TEXT NOT NULL,            -- JSON list
    outline TEXT NOT NULL,               -- JSON list of sections
    notes TEXT NOT NULL,                 -- JSON list / 注意事项
    raw_summary TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS previews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    style_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    pages TEXT NOT NULL,                 -- JSON list of ~6 pages
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS pay_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_id TEXT NOT NULL DEFAULT 'pro_month',
    amount_fen INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'mock_pending',  -- mock_pending | paid | closed | refunded
    wx_prepay_id TEXT,
    wx_transaction_id TEXT,
    notify_payload TEXT,
    paid_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,         -- ppt | exam
    style_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,                -- JSON: slides or exam paper
    status TEXT NOT NULL DEFAULT 'ready', -- generating | ready | failed
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def _migrate(conn: sqlite3.Connection) -> None:
    """Additive migrations for evolving stubs (safe on fresh DB)."""
    if "pay_orders" in {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }:
        cols = _column_names(conn, "pay_orders")
        alters = []
        if "plan_id" not in cols:
            alters.append("ALTER TABLE pay_orders ADD COLUMN plan_id TEXT NOT NULL DEFAULT 'pro_month'")
        if "wx_transaction_id" not in cols:
            alters.append("ALTER TABLE pay_orders ADD COLUMN wx_transaction_id TEXT")
        if "notify_payload" not in cols:
            alters.append("ALTER TABLE pay_orders ADD COLUMN notify_payload TEXT")
        if "paid_at" not in cols:
            alters.append("ALTER TABLE pay_orders ADD COLUMN paid_at TEXT")
        if "updated_at" not in cols:
            alters.append("ALTER TABLE pay_orders ADD COLUMN updated_at TEXT")
        for sql in alters:
            conn.execute(sql)


def ensure_db() -> None:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    ensure_db()
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def loads(text: str | None, default: Any = None) -> Any:
    if not text:
        return default
    return json.loads(text)
