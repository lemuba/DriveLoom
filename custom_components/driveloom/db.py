"""Single SQLite store for DriveLoom's own persistent data.

Home Assistant configuration entries and entity registries remain owned by HA.
This store deliberately never reads data from the old integration.
"""

from __future__ import annotations

import json
import sqlite3
import zlib
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from homeassistant.core import HomeAssistant


DB_FILENAME = "driveloom.db"


def db_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(".storage", DB_FILENAME))


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA foreign_keys=ON")
    return con


@lru_cache(maxsize=16)
def initialize(path: Path) -> None:
    with connect(path) as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS integration_state (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_history (
                vehicle_id TEXT NOT NULL,
                day TEXT NOT NULL,
                value_json TEXT NOT NULL,
                PRIMARY KEY (vehicle_id, day)
            );
            CREATE TABLE IF NOT EXISTS cache_state (
                key TEXT PRIMARY KEY,
                value_blob BLOB NOT NULL
            );
            CREATE TABLE IF NOT EXISTS vehicle_samples (
                vehicle_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                ts REAL NOT NULL,
                value REAL,
                unit TEXT,
                PRIMARY KEY (vehicle_id, metric, ts)
            );
            CREATE INDEX IF NOT EXISTS idx_vehicle_samples_time
                ON vehicle_samples(vehicle_id, ts);
        """)
        if con.execute("PRAGMA user_version").fetchone()[0] == 0:
            con.execute("PRAGMA user_version=1")


def read_cache(path: Path, key: str) -> dict[str, Any] | None:
    initialize(path)
    with connect(path) as con:
        row = con.execute("SELECT value_blob FROM cache_state WHERE key=?", (key,)).fetchone()
        return json.loads(zlib.decompress(row[0])) if row else None


def write_cache(path: Path, key: str, payload: dict[str, Any]) -> None:
    initialize(path)
    value = zlib.compress(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(), 5)
    with connect(path) as con:
        con.execute(
            "INSERT INTO cache_state(key, value_blob) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value_blob=excluded.value_blob",
            (key, value),
        )


def write_samples(
    path: Path, vehicle_id: str, samples: list[tuple[str, float, float | None, str | None]]
) -> None:
    """Store raw source readings and derived counters with their observation time."""
    if not samples:
        return
    initialize(path)
    with connect(path) as con:
        con.executemany(
            "INSERT INTO vehicle_samples(vehicle_id,metric,ts,value,unit) VALUES (?,?,?,?,?) "
            "ON CONFLICT(vehicle_id,metric,ts) DO UPDATE SET "
            "value=excluded.value,unit=excluded.unit",
            ((vehicle_id, metric, ts, value, unit) for metric, ts, value, unit in samples),
        )


def read_samples(
    path: Path, vehicle_id: str, metrics: list[str], start: datetime, end: datetime
) -> dict[str, list[Any]]:
    """Return one held value before start, followed by samples in the period."""
    initialize(path)
    result: dict[str, list[Any]] = {}
    with connect(path) as con:
        for metric in metrics:
            before = con.execute(
                "SELECT ts,value,unit FROM vehicle_samples "
                "WHERE vehicle_id=? AND metric=? AND ts<=? ORDER BY ts DESC LIMIT 1",
                (vehicle_id, metric, start.timestamp()),
            ).fetchone()
            rows = ([before] if before else []) + con.execute(
                "SELECT ts,value,unit FROM vehicle_samples "
                "WHERE vehicle_id=? AND metric=? AND ts>? AND ts<=? ORDER BY ts",
                (vehicle_id, metric, start.timestamp(), end.timestamp()),
            ).fetchall()
            result[metric] = [
                SimpleNamespace(
                    state=str(row["value"]) if row["value"] is not None else "unavailable",
                    last_updated=datetime.fromtimestamp(row["ts"], tz=timezone.utc),
                    attributes={"unit_of_measurement": row["unit"]},
                )
                for row in rows
            ]
    return result


class SQLiteStore:
    """Keep the existing async Store interface while moving its contents to SQLite."""

    def __init__(
        self, hass: HomeAssistant, key: str, *, vehicle_id: str | None = None
    ) -> None:
        self.hass = hass
        self.path = db_path(hass)
        self.key = key
        self.vehicle_id = vehicle_id

    def _load(self) -> dict[str, Any] | None:
        initialize(self.path)
        with connect(self.path) as con:
            row = con.execute(
                "SELECT value_json FROM integration_state WHERE key=?", (self.key,)
            ).fetchone()
            if row is None:
                data: dict[str, Any] | None = None
            else:
                data = json.loads(row["value_json"])
            if self.vehicle_id is not None:
                ledger = {
                    row["day"]: json.loads(row["value_json"])
                    for row in con.execute(
                        "SELECT day, value_json FROM daily_history WHERE vehicle_id=?",
                        (self.vehicle_id,),
                    )
                }
                if data is not None or ledger:
                    data = data or {}
                    data["daily_history"] = ledger
            return data

    async def async_load(self) -> dict[str, Any] | None:
        return await self.hass.async_add_executor_job(self._load)

    def _save(self, data: dict[str, Any]) -> None:
        initialize(self.path)
        payload = dict(data)
        ledger = payload.pop("daily_history", {}) if self.vehicle_id is not None else None
        if ledger is not None and not isinstance(ledger, dict):
            raise ValueError("daily_history must be a dictionary")
        with connect(self.path) as con:
            con.execute(
                "INSERT INTO integration_state(key, value_json) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
                (self.key, json.dumps(payload, ensure_ascii=False, allow_nan=False)),
            )
            if ledger is not None:
                existing = {
                    row["day"]: row["value_json"]
                    for row in con.execute(
                        "SELECT day, value_json FROM daily_history WHERE vehicle_id=?",
                        (self.vehicle_id,),
                    )
                }
                for day in existing.keys() - ledger.keys():
                    con.execute(
                        "DELETE FROM daily_history WHERE vehicle_id=? AND day=?",
                        (self.vehicle_id, day),
                    )
                for day, values in ledger.items():
                    encoded = json.dumps(values, ensure_ascii=False, allow_nan=False)
                    if existing.get(day) != encoded:
                        con.execute(
                            "INSERT INTO daily_history(vehicle_id, day, value_json) "
                            "VALUES (?, ?, ?) ON CONFLICT(vehicle_id, day) "
                            "DO UPDATE SET value_json=excluded.value_json",
                            (self.vehicle_id, day, encoded),
                        )

    async def async_save(self, data: dict[str, Any]) -> None:
        await self.hass.async_add_executor_job(self._save, data)
