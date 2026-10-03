"""Bounded, independent SQLite snapshot cache for public OCPDB POIs.

Only complete page sets are stored. Database work runs in HA's executor.
"""

from __future__ import annotations

import json
import sqlite3
import zlib
from pathlib import Path
from typing import Any

DB_FILENAME = "driveloom-ocpdb.db"
MAX_SNAPSHOTS = 6


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("CREATE TABLE IF NOT EXISTS snapshots ("
               "key TEXT PRIMARY KEY, stored_at REAL NOT NULL, payload BLOB NOT NULL)")
    return db


def read(path: Path, key: str) -> tuple[float, dict[str, Any]] | None:
    if not path.exists():
        return None
    with _connect(path) as db:
        row = db.execute("SELECT stored_at,payload FROM snapshots WHERE key=?", (key,)).fetchone()
    if row is None:
        return None
    return float(row[0]), json.loads(zlib.decompress(row[1]))


def write(path: Path, key: str, stored_at: float, snapshot: dict[str, Any]) -> None:
    payload = zlib.compress(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode(), 5)
    with _connect(path) as db:
        db.execute("INSERT OR REPLACE INTO snapshots(key,stored_at,payload) VALUES (?,?,?)",
                   (key, stored_at, payload))
        db.execute("DELETE FROM snapshots WHERE key NOT IN ("
                   "SELECT key FROM snapshots ORDER BY stored_at DESC LIMIT ?)", (MAX_SNAPSHOTS,))
        db.commit()
