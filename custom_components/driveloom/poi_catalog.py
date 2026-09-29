"""Regional, persistent OSM POI catalogue for the DriveLoom map.

Import a published regional extract in a worker thread. Readers only see the
previous complete SQLite file until the new catalogue has been committed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import sqlite3
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .db import SQLiteStore
from .poi import POI_CLAUSES, _haversine_m

_LOGGER = logging.getLogger(__name__)
STORE_KEY = f"{DOMAIN}.poi_catalog_settings"
DATA_MANAGER = "poi_catalog_manager"
REGIONS = {
    "germany": ("Deutschland", "europe/germany"),
    **{
        slug: (label, f"europe/germany/{slug}")
        for slug, label in (
            ("baden-wuerttemberg", "Baden-Württemberg"),
            ("bayern", "Bayern"),
            ("berlin", "Berlin"),
            ("brandenburg", "Brandenburg"),
            ("bremen", "Bremen"),
            ("hamburg", "Hamburg"),
            ("hessen", "Hessen"),
            ("mecklenburg-vorpommern", "Mecklenburg-Vorpommern"),
            ("niedersachsen", "Niedersachsen"),
            ("nordrhein-westfalen", "Nordrhein-Westfalen"),
            ("rheinland-pfalz", "Rheinland-Pfalz"),
            ("saarland", "Saarland"),
            ("sachsen", "Sachsen"),
            ("sachsen-anhalt", "Sachsen-Anhalt"),
            ("schleswig-holstein", "Schleswig-Holstein"),
            ("thueringen", "Thüringen"),
        )
    },
}
DEFAULT_SETTINGS = {"region": "", "hour": 2, "interval_days": 1}
MAX_DOWNLOAD_BYTES = 8 * 1024**3

# Keep the frontend's most specific category precedence. The POI filter
# template is evaluated against the resulting category at query time.
_PRIORITY = (
    "charging", "fuel", "workshop", "car_wash", "tyres", "car_parts",
    "car_rental", "park_ride", "parking_garage", "parking",
)
_CATEGORY_ORDER = (*_PRIORITY, *(key for key in POI_CLAUSES if key not in _PRIORITY))
_TAG_FILTERS = {
    category: [
        [(key, value, operator == "~") for key, operator, value in re.findall(
            r'\["([^"]+)"(=|~)"([^"]+)"\]', clause
        )]
        for clause in POI_CLAUSES[category]
    ]
    for category in POI_CLAUSES
}


def _category(tags: dict[str, str]) -> str | None:
    for category in _CATEGORY_ORDER:
        if category == "charging":  # OCM is the established charging source.
            continue
        for clause in _TAG_FILTERS[category]:
            if all(
                (re.search(value, tags.get(key, "")) if regex else tags.get(key) == value)
                for key, value, regex in clause
            ):
                return category
    return None


def _normal(text: str) -> str:
    expanded = unicodedata.normalize("NFKD", text.casefold().replace("ß", "ss"))
    return "".join(char for char in expanded if char.isalnum() and not unicodedata.combining(char))


def _build_catalog(source: Path, target: Path, region: str) -> int:
    """Stream a PBF into an indexed SQLite database without retaining all POIs."""
    import osmium  # HA installs this pinned dependency from the manifest.

    connection = sqlite3.connect(target)
    try:
        connection.executescript("""
            PRAGMA journal_mode=DELETE;
            PRAGMA synchronous=NORMAL;
            CREATE TABLE pois (
                id INTEGER PRIMARY KEY, osm_type TEXT NOT NULL, osm_id INTEGER NOT NULL,
                category TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
                tags TEXT NOT NULL, search_text TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE positions USING rtree(id, min_lat, max_lat, min_lon, max_lon);
            CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        batch: list[tuple[Any, ...]] = []
        count = 0

        def flush() -> None:
            nonlocal count
            if not batch:
                return
            connection.executemany(
                "INSERT INTO pois(osm_type,osm_id,category,lat,lon,tags,search_text) "
                "VALUES (?,?,?,?,?,?,?)", batch
            )
            first = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            # executemany assigns contiguous ROWIDs for this exclusive writer.
            connection.executemany(
                "INSERT INTO positions VALUES (?,?,?,?,?)",
                ((first - len(batch) + i + 1, row[3], row[3], row[4], row[4])
                 for i, row in enumerate(batch)),
            )
            count += len(batch)
            batch.clear()

        class Handler(osmium.SimpleHandler):
            def add(self, obj: Any, kind: str, lat: float, lon: float) -> None:
                tags = dict(obj.tags)
                category = _category(tags)
                if category is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    return
                # Preserve OSM tags required by the current map detail panel.
                retained = {
                    key: value for key, value in tags.items()
                    if key in {"name", "brand", "operator", "network", "amenity", "shop",
                               "craft", "parking", "park_ride", "tourism", "highway",
                               "leisure", "healthcare", "historic", "railway", "aeroway",
                               "emergency", "opening_hours", "capacity", "phone",
                               "website", "access", "fee", "cuisine", "ref"}
                    or key.startswith(("addr:", "contact:"))
                }
                words = " ".join(
                    str(tags.get(key, "")) for key in
                    ("name", "brand", "operator", "network", "cuisine",
                     "addr:street", "addr:city", "addr:postcode", "addr:housename")
                )
                batch.append((kind, int(obj.id), category, lat, lon,
                              json.dumps(retained, ensure_ascii=False), _normal(words)))
                if len(batch) >= 2000:
                    flush()

            def node(self, node: Any) -> None:
                if node.location.valid():
                    self.add(node, "node", node.location.lat, node.location.lon)

            def way(self, way: Any) -> None:
                if not way.tags:
                    return
                points = [(ref.location.lat, ref.location.lon) for ref in way.nodes
                          if ref.location.valid()]
                if points:
                    self.add(way, "way",
                             sum(point[0] for point in points) / len(points),
                             sum(point[1] for point in points) / len(points))

        locations = osmium.NodeLocationsForWays(osmium.index.create_map("flex_mem"))
        # Regional extracts may omit some nodes on their boundary. Keep every
        # valid coordinate on those ways instead of failing the entire import.
        locations.ignore_errors()
        osmium.apply(str(source), locations, Handler())
        flush()
        if count == 0:
            raise ValueError("Der OSM-Auszug enthält keine unterstützten POIs")
        connection.execute("INSERT INTO meta VALUES (?,?)", ("region", region))
        connection.execute("INSERT INTO meta VALUES (?,?)", ("count", str(count)))
        connection.execute("INSERT INTO meta VALUES (?,?)", ("updated", str(time.time())))
        connection.commit()
        return count
    finally:
        connection.close()


def _query(path: Path, region: str, latitude: float, longitude: float,
           radius_km: int, categories: list[str], search: str, limit: int,
           bounds: tuple[float, float, float, float] | None = None) -> tuple[list[dict[str, Any]], int]:
    if not path.exists() or not categories:
        return [], 0
    lat_delta = radius_km / 110.574
    lon_delta = radius_km / max(1.0, 111.320 * abs(math.cos(math.radians(latitude))))
    min_lat, max_lat = max(-90, latitude - lat_delta), min(90, latitude + lat_delta)
    min_lon, max_lon = max(-180, longitude - lon_delta), min(180, longitude + lon_delta)
    if bounds:
        south, west, north, east = bounds
        min_lat, max_lat = max(min_lat, south), min(max_lat, north)
        min_lon, max_lon = max(min_lon, west), min(max_lon, east)
    if min_lat > max_lat or min_lon > max_lon:
        return [], 0
    # One connection per read makes atomic file replacement safe for active users.
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=15)
    try:
        stored = connection.execute(
            "SELECT value FROM meta WHERE key='region'"
        ).fetchone()
        if not stored or stored[0] != region:
            return [], 0
        placeholders = ",".join("?" for _ in categories)
        # Filter categories and indexed bounding box before ranking. Ranking in
        # SQL bounds the rows transferred to Python even for country extracts.
        sql = f"""
            SELECT p.osm_type,p.osm_id,p.lat,p.lon,p.tags
            FROM positions AS r JOIN pois AS p ON p.id=r.id
            WHERE r.max_lat>=? AND r.min_lat<=? AND r.max_lon>=? AND r.min_lon<=?
              AND p.category IN ({placeholders})
              AND (?='' OR p.search_text LIKE '%' || ? || '%')
            ORDER BY ((p.lat-?)*(p.lat-?) + (p.lon-?)*(p.lon-?)*?)
            LIMIT ?
        """
        needle = _normal(search)
        cosine = max(0.01, math.cos(math.radians(latitude)) ** 2)
        rows = connection.execute(sql, (
            min_lat, max_lat, min_lon, max_lon, *categories, needle, needle,
            latitude, latitude, longitude, longitude, cosine, limit * 3,
        )).fetchall()
        result = [
            {"type": kind, "id": osm_id, "lat": lat, "lon": lon,
             "tags": json.loads(tags), "provider": "osm"}
            for kind, osm_id, lat, lon, tags in rows
            if _haversine_m(latitude, longitude, lat, lon) <= radius_km * 1000
        ]
        return result[:limit], len(rows)
    finally:
        connection.close()


class PoiCatalog:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.path = Path(hass.config.path(".storage", "driveloom-pois.db"))
        self.store = SQLiteStore(hass, STORE_KEY)
        self.settings = dict(DEFAULT_SETTINGS)
        self.task: asyncio.Task | None = None
        self.cancel_timer: Any = None
        self.error = ""

    async def async_setup(self) -> None:
        stored = await self.store.async_load() or {}
        if isinstance(stored, dict):
            for key in DEFAULT_SETTINGS:
                if key in stored:
                    self.settings[key] = stored[key]
        if self.settings["region"] not in ("", *REGIONS):
            self.settings["region"] = ""
        if not isinstance(self.settings["hour"], int) or not 0 <= self.settings["hour"] <= 23:
            self.settings["hour"] = 2
        if not isinstance(self.settings["interval_days"], int) or not 1 <= self.settings["interval_days"] <= 30:
            self.settings["interval_days"] = 1
        self.schedule()
        if self.settings["region"]:
            self.hass.async_create_task(self.async_refresh_if_due())

    def schedule(self) -> None:
        if self.cancel_timer:
            self.cancel_timer()
            self.cancel_timer = None
        if self.settings["region"]:
            self.cancel_timer = async_track_time_change(
                self.hass, self._on_timer, hour=int(self.settings["hour"]), minute=0, second=0
            )

    def _on_timer(self, _now: datetime) -> None:
        self.hass.async_create_task(self.async_refresh_if_due())

    def status(self) -> dict[str, Any]:
        info: dict[str, Any] = {"settings": dict(self.settings),
                                "updating": self.task is not None and not self.task.done(),
                                "error": self.error}
        if self.path.exists():
            try:
                with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as con:
                    info["region"] = con.execute("SELECT value FROM meta WHERE key='region'").fetchone()[0]
                    info["count"] = int(con.execute("SELECT value FROM meta WHERE key='count'").fetchone()[0])
                    info["updated"] = float(con.execute("SELECT value FROM meta WHERE key='updated'").fetchone()[0])
            except (sqlite3.Error, TypeError, IndexError):
                _LOGGER.exception("Could not read DriveLoom POI catalogue status")
        return info

    async def async_refresh_if_due(self) -> None:
        status = await self.hass.async_add_executor_job(self.status)
        if status.get("region") == self.settings["region"] and (
            time.time() - status.get("updated", 0) <
            int(self.settings["interval_days"]) * 86400
        ):
            return
        await self.async_refresh()

    async def async_refresh(self) -> None:
        if not self.settings["region"]:
            return
        if self.task and not self.task.done():
            return await asyncio.shield(self.task)
        requested_region = self.settings["region"]
        self.task = self.hass.async_create_task(self._download_and_import())
        try:
            await asyncio.shield(self.task)
        finally:
            if self.task and self.task.done():
                self.task = None
            if self.settings["region"] and self.settings["region"] != requested_region:
                self.hass.async_create_task(self.async_refresh_if_due())

    async def _download_and_import(self) -> None:
        region = self.settings["region"]
        url = f"https://download.geofabrik.de/{REGIONS[region][1]}-latest.osm.pbf"
        source = self.path.with_suffix(".download.pbf")
        target = self.path.with_suffix(".new.db")
        await self.hass.async_add_executor_job(self.path.parent.mkdir, 0o777, True, True)
        await self.hass.async_add_executor_job(source.unlink, True)
        await self.hass.async_add_executor_job(target.unlink, True)
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(url, timeout=None) as response:
                response.raise_for_status()
                length = int(response.headers.get("Content-Length", 0))
                if length > MAX_DOWNLOAD_BYTES:
                    raise ValueError("OSM-Auszug ist größer als 8 GiB")
                size = 0
                handle = await self.hass.async_add_executor_job(source.open, "wb")
                try:
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_DOWNLOAD_BYTES:
                            raise ValueError("OSM-Auszug ist größer als 8 GiB")
                        await self.hass.async_add_executor_job(handle.write, chunk)
                finally:
                    await self.hass.async_add_executor_job(handle.close)
            if size < 100:
                raise ValueError("Unvollständiger OSM-Auszug")
            count = await self.hass.async_add_executor_job(_build_catalog, source, target, region)
            await self.hass.async_add_executor_job(os.replace, target, self.path)
            self.error = ""
            _LOGGER.info("DriveLoom POI catalogue: %s POIs in %s", count, region)
        except Exception as err:
            self.error = str(err)
            _LOGGER.warning("DriveLoom POI catalogue refresh failed: %s", err)
            raise
        finally:
            await self.hass.async_add_executor_job(source.unlink, True)
            await self.hass.async_add_executor_job(target.unlink, True)

    async def async_query(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        region = self.settings["region"]
        status = await self.hass.async_add_executor_job(self.status)
        if not region or status.get("region") != region:
            return None
        bounds = msg.get("viewport")
        bbox = tuple(bounds) if bounds else None
        maximum = int(msg["max_results"])
        nearby_count = min(maximum, 1000, max(20, maximum // 4)) if bbox else maximum
        nearby, nearby_examined = await self.hass.async_add_executor_job(
            _query, self.path, region, float(msg["latitude"]), float(msg["longitude"]),
            int(msg["radius_km"]), [key for key in msg["categories"] if key != "charging"],
            str(msg.get("search_filter", "")), nearby_count, None,
        )
        elements = nearby
        examined = nearby_examined
        if bbox and maximum > nearby_count:
            visible, visible_examined = await self.hass.async_add_executor_job(
                _query, self.path, region, float(msg["latitude"]), float(msg["longitude"]),
                int(msg["radius_km"]), [key for key in msg["categories"] if key != "charging"],
                str(msg.get("search_filter", "")), maximum - nearby_count, bbox,
            )
            seen = {(item["type"], item["id"]) for item in nearby}
            elements.extend(item for item in visible if (item["type"], item["id"]) not in seen)
            examined += visible_examined
        elements.sort(key=lambda item: _haversine_m(
            float(msg["latitude"]), float(msg["longitude"]), item["lat"], item["lon"]
        ))
        return {
            "elements": elements, "endpoint": f"OSM-Katalog {REGIONS[region][0]}",
            "sources": [f"Geofabrik / OpenStreetMap ({REGIONS[region][0]})"],
            "warnings": [], "charging_status": "unused", "retry_after_seconds": 0,
            "candidate_limit_hit": len(elements) >= maximum,
            "candidate_limit": int(msg["max_results"]), "cached": True,
            "updated": status.get("updated"), "elapsed_ms": 0,
        }


def manager(hass: HomeAssistant) -> PoiCatalog:
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_MANAGER not in data:
        data[DATA_MANAGER] = PoiCatalog(hass)
    return data[DATA_MANAGER]


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/poi_catalog/status"})
@websocket_api.async_response
async def websocket_status(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                           msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], await hass.async_add_executor_job(manager(hass).status))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/poi_catalog/configure",
    vol.Required("region"): vol.In(tuple(["", *REGIONS])),
    vol.Required("hour"): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
    vol.Required("interval_days"): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
})
@websocket_api.async_response
async def websocket_configure(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                              msg: dict[str, Any]) -> None:
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Nur Administratoren können den Katalog konfigurieren")
        return
    catalog = manager(hass)
    catalog.settings = {key: msg[key] for key in DEFAULT_SETTINGS}
    await catalog.store.async_save(catalog.settings)
    catalog.schedule()
    if catalog.settings["region"]:
        hass.async_create_task(catalog.async_refresh_if_due())
    connection.send_result(msg["id"], await hass.async_add_executor_job(catalog.status))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/poi_catalog/refresh"})
@websocket_api.async_response
async def websocket_refresh(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                            msg: dict[str, Any]) -> None:
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Nur Administratoren können den Katalog aktualisieren")
        return
    catalog = manager(hass)
    if not catalog.settings["region"]:
        connection.send_error(msg["id"], "catalog_disabled", "Zuerst eine Region auswählen")
        return
    hass.async_create_task(catalog.async_refresh())
    connection.send_result(msg["id"], await hass.async_add_executor_job(catalog.status))


def async_register_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_status)
    websocket_api.async_register_command(hass, websocket_configure)
    websocket_api.async_register_command(hass, websocket_refresh)
