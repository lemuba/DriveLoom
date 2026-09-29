"""Regional, persistent OSM POI catalogue for the DriveLoom map.

Import a published regional extract in a worker thread. Readers only see the
previous complete SQLite file until the new catalogue has been committed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import hashlib
import os
import re
import shutil
import sqlite3
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .db import SQLiteStore
from .poi import POI_CLAUSES, _haversine_m
from .pbf_reader import entities as pbf_entities

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
DEFAULT_SETTINGS = {"regions": [], "hour": 2, "interval_days": 1}
MAX_DOWNLOAD_BYTES = 64 * 1024**3
INDEX_URL = "https://download.geofabrik.de/index-v1-nogeom.json"
INDEX_TTL_SECONDS = 7 * 24 * 60 * 60
INDEX_MAX_BYTES = 8 * 1024 * 1024
_LEGACY_PATHS = {path: key for key, (_, path) in REGIONS.items()}


def _valid_pbf_url(url: str) -> bool:
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.netloc == "download.geofabrik.de"
            and parsed.path.endswith("-latest.osm.pbf") and not parsed.query
            and not parsed.fragment)


def _parse_index(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Keep only country extracts and the legacy German state extracts."""
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("Ungültiger Geofabrik-Index")
    regions: dict[str, dict[str, str]] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties", {}) if isinstance(feature, dict) else {}
        path = str(props.get("id", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9/_-]{0,110}", path):
            continue
        country_codes = props.get("iso3166-1:alpha2")
        if not (isinstance(country_codes, list) and country_codes) and path not in _LEGACY_PATHS:
            continue
        url = str((props.get("urls") or {}).get("pbf", ""))
        if not _valid_pbf_url(url):
            continue
        key = _LEGACY_PATHS.get(path, path)
        regions[key] = {"name": str(props.get("name", key))[:100], "url": url}
    if len(regions) < 20:
        raise ValueError("Der Geofabrik-Länderindex ist unvollständig")
    return regions


async def _read_index(response: Any) -> bytes:
    """Read the complete streamed response, with a bound on its total size."""
    parts: list[bytes] = []
    size = 0
    async for chunk in response.content.iter_chunked(64 * 1024):
        size += len(chunk)
        if size > INDEX_MAX_BYTES:
            raise ValueError("Der Länderindex ist zu groß")
        parts.append(chunk)
    return b"".join(parts)


async def _save_download(response: Any, handle: Any, hass: HomeAssistant,
                         total: int | None, report: Any) -> int:
    """Stream a country extract to disk and report committed byte counts."""
    size = 0
    async for chunk in response.content.iter_chunked(1024 * 1024):
        size += len(chunk)
        if size > MAX_DOWNLOAD_BYTES:
            raise ValueError("OSM-Auszug ist größer als 64 GiB")
        await hass.async_add_executor_job(handle.write, chunk)
        report(size, total)
    return size


def _merge_country_results(groups: list[list[dict[str, Any]]],
                           latitude: float, longitude: float, limit: int) -> list[dict[str, Any]]:
    unique: dict[tuple[str, int], dict[str, Any]] = {}
    for group in groups:
        for element in group:
            unique.setdefault((element["type"], element["id"]), element)
    return sorted(unique.values(), key=lambda element: _haversine_m(
        latitude, longitude, element["lat"], element["lon"]
    ))[:limit]


def _intersects(bounds: list[float] | None, latitude: float,
                longitude: float, radius_km: int) -> bool:
    if not bounds:
        return True  # v0.1.9 catalogues do not have bounding metadata.
    south, west, north, east = bounds
    lat_delta = radius_km / 110.574
    lon_delta = radius_km / max(1.0, 111.320 * abs(math.cos(math.radians(latitude))))
    return (south <= latitude + lat_delta and north >= latitude - lat_delta
            and west <= longitude + lon_delta and east >= longitude - lon_delta)


def _catalog_path(directory: Path, region: str) -> Path:
    digest = hashlib.sha256(region.encode("utf-8")).hexdigest()[:20]
    return directory / f"driveloom-pois-{digest}.db"


def _stored_catalogs(directory: Path) -> list[dict[str, Any]]:
    """List only complete DriveLoom region files, including deselected ones."""
    if not directory.exists():
        return []
    stored = []
    for path in directory.glob("driveloom-pois-*.db"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
                meta = dict(con.execute("SELECT key,value FROM meta WHERE key IN ('region','count','updated')"))
            region = meta.get("region", "")
            if (not re.fullmatch(r"[a-z0-9][a-z0-9/_-]{0,110}", region)
                    or path != _catalog_path(directory, region)):
                continue
            stored.append({"key": region, "count": int(meta["count"]),
                           "updated": float(meta["updated"]), "bytes": path.stat().st_size})
        except (sqlite3.Error, KeyError, ValueError, OSError):
            _LOGGER.warning("Could not inspect DriveLoom POI catalogue %s", path)
    return sorted(stored, key=lambda item: item["key"])


def _delete_catalog_file(directory: Path, region: str) -> int:
    """Delete exactly one identified complete catalogue; never the main DB."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9/_-]{0,110}", region):
        raise ValueError("Ungültige Region")
    path = _catalog_path(directory, region)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Gespeicherter POI-Katalog nicht gefunden")
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
        row = con.execute("SELECT value FROM meta WHERE key='region'").fetchone()
    if not row or row[0] != region:
        raise ValueError("Katalogdatei gehört nicht zu dieser Region")
    size = path.stat().st_size
    path.unlink()
    return size

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
        min_lat, max_lat, min_lon, max_lon = 90.0, -90.0, 180.0, -180.0

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

        def add(kind: str, osm_id: int, tags: dict[str, str],
                lat: float, lon: float) -> None:
            nonlocal min_lat, max_lat, min_lon, max_lon
            category = _category(tags)
            if category is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return
            retained = {
                key: value for key, value in tags.items()
                if key in {"name", "brand", "operator", "network", "amenity", "shop",
                           "craft", "parking", "park_ride", "tourism", "highway",
                           "leisure", "healthcare", "historic", "railway", "aeroway",
                           "emergency", "opening_hours", "capacity", "phone",
                           "website", "access", "fee", "cuisine", "ref"}
                or key.startswith(("addr:", "contact:"))
            }
            words = " ".join(str(tags.get(key, "")) for key in
                             ("name", "brand", "operator", "network", "cuisine",
                              "addr:street", "addr:city", "addr:postcode", "addr:housename"))
            batch.append((kind, int(osm_id), category, lat, lon,
                          json.dumps(retained, ensure_ascii=False), _normal(words)))
            min_lat, max_lat = min(min_lat, lat), max(max_lat, lat)
            min_lon, max_lon = min(min_lon, lon), max(max_lon, lon)
            if len(batch) >= 2000:
                flush()

        # A locally available osmium can accelerate large extracts. It is
        # deliberately not a manifest requirement: Home Assistant must start
        # even on Python/platform combinations without an osmium wheel.
        try:
            import osmium
        except ImportError:
            osmium = None

        if osmium is not None:
            class Handler(osmium.SimpleHandler):
                def node(self, node: Any) -> None:
                    if node.location.valid():
                        add("node", node.id, dict(node.tags),
                            node.location.lat, node.location.lon)

                def way(self, way: Any) -> None:
                    if not way.tags or _category(dict(way.tags)) is None:
                        return
                    points = [(ref.location.lat, ref.location.lon) for ref in way.nodes
                              if ref.location.valid()]
                    if points:
                        add("way", way.id, dict(way.tags),
                            sum(point[0] for point in points) / len(points),
                            sum(point[1] for point in points) / len(points))

            locations = osmium.NodeLocationsForWays(osmium.index.create_map("flex_mem"))
            locations.ignore_errors()
            osmium.apply(str(source), locations, Handler())
        else:
            # Only references of relevant POI ways are kept for pass two.
            # Temporary SQLite tables disappear when this connection closes.
            connection.executescript("""
                CREATE TEMP TABLE wanted(id INTEGER PRIMARY KEY, lat REAL, lon REAL);
                CREATE TEMP TABLE ways(id INTEGER, tags TEXT, refs TEXT);
            """)
            wanted: set[int] = set()
            way_batch: list[tuple[int, str, str]] = []
            for kind, osm_id, tags, lat_or_refs, lon in pbf_entities(source):
                if kind == "node":
                    if tags:
                        add("node", osm_id, tags, lat_or_refs, lon)
                elif _category(tags) is not None and lat_or_refs:
                    refs = lat_or_refs
                    wanted.update(refs)
                    way_batch.append((osm_id, json.dumps(tags), json.dumps(refs)))
                    if len(way_batch) >= 2000:
                        connection.executemany("INSERT INTO ways VALUES (?,?,?)", way_batch)
                        way_batch.clear()
            connection.executemany("INSERT INTO ways VALUES (?,?,?)", way_batch)
            if wanted:
                coord_batch: list[tuple[int, float, float]] = []
                for kind, osm_id, _, lat, lon in pbf_entities(source, ways=False):
                    if osm_id in wanted:
                        coord_batch.append((osm_id, lat, lon))
                        if len(coord_batch) >= 2000:
                            connection.executemany("INSERT INTO wanted VALUES (?,?,?)", coord_batch)
                            coord_batch.clear()
                connection.executemany("INSERT INTO wanted VALUES (?,?,?)", coord_batch)
                for osm_id, tags_json, refs_json in connection.execute("SELECT * FROM ways"):
                    refs = json.loads(refs_json)
                    # Repeated IDs at a closed polygon have the same weight as
                    # in the osmium importer.
                    points = [point for ref in refs if (point := connection.execute(
                        "SELECT lat,lon FROM wanted WHERE id=?", (ref,)
                    ).fetchone()) is not None]
                    if points:
                        add("way", osm_id, json.loads(tags_json),
                            sum(point[0] for point in points) / len(points),
                            sum(point[1] for point in points) / len(points))
            connection.executescript("DROP TABLE ways; DROP TABLE wanted;")
        flush()
        if count == 0:
            raise ValueError("Der OSM-Auszug enthält keine unterstützten POIs")
        connection.execute("INSERT INTO meta VALUES (?,?)", ("region", region))
        connection.execute("INSERT INTO meta VALUES (?,?)", ("count", str(count)))
        connection.execute("INSERT INTO meta VALUES (?,?)", ("updated", str(time.time())))
        connection.execute("INSERT INTO meta VALUES (?,?)",
                           ("bounds", json.dumps([min_lat, min_lon, max_lat, max_lon])))
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
        self.directory = Path(hass.config.path(".storage"))
        self.legacy_path = self.directory / "driveloom-pois.db"
        self.store = SQLiteStore(hass, STORE_KEY)
        self.index_store = SQLiteStore(hass, f"{DOMAIN}.poi_catalog_index")
        self.settings = {"regions": [], "hour": 2, "interval_days": 1}
        self.available = {
            key: {"name": name, "url": f"https://download.geofabrik.de/{path}-latest.osm.pbf"}
            for key, (name, path) in REGIONS.items()
        }
        self.index_updated = 0.0
        self.index_error = ""
        self.task: asyncio.Task | None = None
        self.index_task: asyncio.Task | None = None
        self.current_region = ""
        self.progress: dict[str, Any] = {}
        self.cancel_timer: Any = None
        self.errors: dict[str, str] = {}

    def path_for(self, region: str) -> Path:
        return _catalog_path(self.directory, region)

    async def async_setup(self) -> None:
        stored = await self.store.async_load() or {}
        if isinstance(stored, dict):
            if isinstance(stored.get("regions"), list):
                self.settings["regions"] = [
                    key for key in dict.fromkeys(stored["regions"])
                    if isinstance(key, str) and re.fullmatch(r"[a-z0-9][a-z0-9/_-]{0,110}", key)
                ]
            elif stored.get("region") in REGIONS:
                # v0.1.9 stored one region. Its database is migrated below.
                self.settings["regions"] = [stored["region"]]
            for key in ("hour", "interval_days"):
                if key in stored:
                    self.settings[key] = stored[key]
        if not isinstance(self.settings["hour"], int) or not 0 <= self.settings["hour"] <= 23:
            self.settings["hour"] = 2
        if not isinstance(self.settings["interval_days"], int) or not 1 <= self.settings["interval_days"] <= 30:
            self.settings["interval_days"] = 1
        cached_index = await self.index_store.async_load() or {}
        if isinstance(cached_index, dict):
            for key, item in (cached_index.get("regions") or {}).items():
                if (isinstance(key, str) and re.fullmatch(r"[a-z0-9][a-z0-9/_-]{0,110}", key)
                        and isinstance(item, dict)
                        and _valid_pbf_url(str(item.get("url", "")))):
                    self.available[key] = {"name": str(item.get("name", key))[:100],
                                           "url": item["url"]}
            self.index_updated = float(cached_index.get("updated", 0) or 0)
        await self.hass.async_add_executor_job(self._migrate_legacy_file)
        self.schedule()
        self.hass.async_create_task(self.async_update_index_if_due())
        if self.settings["regions"]:
            self.hass.async_create_task(self.async_refresh_all())

    def _migrate_legacy_file(self) -> None:
        if not self.legacy_path.exists():
            return
        try:
            with sqlite3.connect(f"file:{self.legacy_path}?mode=ro", uri=True) as con:
                row = con.execute("SELECT value FROM meta WHERE key='region'").fetchone()
            if row and row[0] in REGIONS:
                destination = self.path_for(row[0])
                if not destination.exists():
                    os.replace(self.legacy_path, destination)
                    return
            _LOGGER.warning("DriveLoom legacy POI catalogue was retained at %s", self.legacy_path)
        except (sqlite3.Error, OSError):
            _LOGGER.exception("Could not migrate DriveLoom v0.1.9 POI catalogue")

    def schedule(self) -> None:
        if self.cancel_timer:
            self.cancel_timer()
            self.cancel_timer = None
        if self.settings["regions"]:
            self.cancel_timer = async_track_time_change(
                self.hass, self._on_timer, hour=int(self.settings["hour"]), minute=0, second=0
            )

    def _on_timer(self, _now: datetime) -> None:
        self.hass.async_create_task(self.async_refresh_all())

    async def async_update_index_if_due(self, *, force: bool = False) -> None:
        if not force and self.index_updated and time.time() - self.index_updated < INDEX_TTL_SECONDS:
            return
        if self.index_task and not self.index_task.done():
            return await asyncio.shield(self.index_task)
        self.index_task = self.hass.async_create_task(self._fetch_index())
        try:
            await asyncio.shield(self.index_task)
        finally:
            if self.index_task.done():
                self.index_task = None

    async def _fetch_index(self) -> None:
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(35):
                async with session.get(INDEX_URL) as response:
                    response.raise_for_status()
                    body = await _read_index(response)
            available = _parse_index(json.loads(body))
            self.available.update(available)
            self.index_updated = time.time()
            self.index_error = ""
            await self.index_store.async_save({
                "regions": available, "updated": self.index_updated
            })
        except Exception as err:
            self.index_error = str(err)
            _LOGGER.warning("DriveLoom country index unavailable: %s", err)

    def _region_status(self, region: str) -> dict[str, Any]:
        info: dict[str, Any] = {
            "updating": self.current_region == region,
            "error": self.errors.get(region, ""),
        }
        path = self.path_for(region)
        if path.exists():
            try:
                with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
                    stored = con.execute("SELECT value FROM meta WHERE key='region'").fetchone()
                    if stored and stored[0] == region:
                        info["count"] = int(con.execute("SELECT value FROM meta WHERE key='count'").fetchone()[0])
                        info["updated"] = float(con.execute("SELECT value FROM meta WHERE key='updated'").fetchone()[0])
                        row = con.execute("SELECT value FROM meta WHERE key='bounds'").fetchone()
                        info["bounds"] = json.loads(row[0]) if row else None
            except (sqlite3.Error, TypeError, IndexError):
                _LOGGER.exception("Could not read DriveLoom POI catalogue %s", region)
        return info

    def status(self) -> dict[str, Any]:
        selected = list(self.settings["regions"])
        details = {region: self._region_status(region) for region in selected}
        return {
            "settings": {**self.settings, "regions": selected},
            "regions": details,
            "stored": [
                {**item, "name": self.available.get(item["key"], {}).get("name", item["key"]),
                 "selected": item["key"] in selected}
                for item in _stored_catalogs(self.directory)
            ],
            "available": [
                {"key": key, "name": item["name"]}
                for key, item in sorted(self.available.items(),
                                        key=lambda pair: pair[1]["name"].casefold())
            ],
            "updating": self.task is not None and not self.task.done(),
            "progress": dict(self.progress),
            "index_updating": self.index_task is not None and not self.index_task.done(),
            "index_error": self.index_error,
        }

    async def async_refresh_all(self, *, force: bool = False, only: str = "") -> None:
        if not self.settings["regions"]:
            return
        if self.task and not self.task.done():
            return await asyncio.shield(self.task)
        requested = tuple(self.settings["regions"])
        self.task = self.hass.async_create_task(self._refresh_selected(requested, force, only))
        try:
            await asyncio.shield(self.task)
        finally:
            if self.task and self.task.done():
                self.task = None
            if any(key not in requested for key in self.settings["regions"]):
                self.hass.async_create_task(self.async_refresh_all())

    async def _refresh_selected(self, selected: tuple[str, ...], force: bool,
                                only: str) -> None:
        await self.async_update_index_if_due()
        for region in selected:
            if region not in self.settings["regions"] or (only and region != only):
                continue
            status = await self.hass.async_add_executor_job(self._region_status, region)
            if (not force and status.get("updated")
                    and time.time() - status["updated"] <
                    self.settings["interval_days"] * 86400):
                continue
            self.current_region = region
            try:
                await self._download_and_import(region)
                self.errors.pop(region, None)
            except Exception as err:
                self.errors[region] = str(err)
                _LOGGER.warning("DriveLoom POI country %s failed: %s", region, err)
            finally:
                self.current_region = ""
                self.progress = {}

    async def _download_and_import(self, region: str) -> None:
        info = self.available.get(region)
        if not info or not _valid_pbf_url(info["url"]):
            raise RuntimeError("Für dieses Land ist derzeit kein OSM-Auszug verfügbar")
        path = self.path_for(region)
        source = path.with_suffix(".download.pbf")
        target = path.with_suffix(".new.db")
        self.progress = {"region": region, "stage": "download", "downloaded": 0, "total": None}
        await self.hass.async_add_executor_job(self.directory.mkdir, 0o777, True, True)
        await self.hass.async_add_executor_job(source.unlink, True)
        await self.hass.async_add_executor_job(target.unlink, True)
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(info["url"], timeout=None) as response:
                response.raise_for_status()
                length = int(response.headers.get("Content-Length", 0))
                if length > MAX_DOWNLOAD_BYTES:
                    raise ValueError("OSM-Auszug ist größer als 64 GiB")
                if length:
                    disk = await self.hass.async_add_executor_job(shutil.disk_usage, self.directory)
                    if disk.free < length * 2:
                        raise ValueError("Zu wenig freier Speicher für Download und neuen Katalog")
                size = 0
                handle = await self.hass.async_add_executor_job(source.open, "wb")
                try:
                    def report(downloaded: int, total: int | None) -> None:
                        self.progress = {"region": region, "stage": "download",
                                         "downloaded": downloaded, "total": total}

                    size = await _save_download(response, handle, self.hass, length or None, report)
                finally:
                    await self.hass.async_add_executor_job(handle.close)
            if size < 100:
                raise ValueError("Unvollständiger OSM-Auszug")
            self.progress = {"region": region, "stage": "import", "downloaded": size,
                             "total": length or None}
            count = await self.hass.async_add_executor_job(_build_catalog, source, target, region)
            await self.hass.async_add_executor_job(os.replace, target, path)
            _LOGGER.info("DriveLoom POI catalogue: %s POIs in %s", count, region)
        finally:
            await self.hass.async_add_executor_job(source.unlink, True)
            await self.hass.async_add_executor_job(target.unlink, True)

    async def async_query(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        selected = list(self.settings["regions"])
        if not selected:
            return None
        statuses = await self.hass.async_add_executor_job(
            lambda: {key: self._region_status(key) for key in selected}
        )
        available = [key for key in selected if statuses[key].get("updated")]
        if not available:
            return None
        bounds = msg.get("viewport")
        bbox = tuple(bounds) if bounds else None
        maximum = int(msg["max_results"])
        latitude, longitude = float(msg["latitude"]), float(msg["longitude"])
        ready = [key for key in available if _intersects(
            statuses[key].get("bounds"), latitude, longitude, int(msg["radius_km"])
        )]
        if not ready:
            return {
                "elements": [], "endpoint": "OSM-Katalog", "sources": [],
                "warnings": ["Keine ausgewählte Region deckt diesen Suchkreis ab"],
                "charging_status": "unused", "retry_after_seconds": 0,
                "candidate_limit_hit": False, "candidate_limit": maximum,
                "cached": True, "elapsed_ms": 0,
            }
        quota = max(20, math.ceil(maximum / len(ready)))
        nearby_quota = min(quota, 1000, max(10, quota // 4)) if bbox else quota
        groups: list[list[dict[str, Any]]] = []
        for region in ready:
            path = self.path_for(region)
            args = (path, region, latitude, longitude, int(msg["radius_km"]),
                    [key for key in msg["categories"] if key != "charging"],
                    str(msg.get("search_filter", "")))
            nearby, _ = await self.hass.async_add_executor_job(
                _query, *args, nearby_quota, None
            )
            groups.append(nearby)
            if bbox and quota > nearby_quota:
                visible, _ = await self.hass.async_add_executor_job(
                    _query, *args, quota - nearby_quota, bbox
                )
                groups.append(visible)
        elements = _merge_country_results(groups, latitude, longitude, maximum)
        missing = [key for key in selected if key not in available]
        return {
            "elements": elements, "endpoint": f"OSM-Katalog ({len(ready)} Länder/Regionen)",
            "sources": [f"Geofabrik / OpenStreetMap ({self.available.get(key, {}).get('name', key)})"
                        for key in ready],
            "warnings": [f"POI-Katalog für {key} wird noch aufgebaut" for key in missing],
            "charging_status": "unused", "retry_after_seconds": 0,
            "candidate_limit_hit": len(elements) >= maximum,
            "candidate_limit": maximum, "cached": True, "elapsed_ms": 0,
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
    vol.Required("regions"): vol.All(
        [vol.All(str, vol.Length(min=1, max=111))], vol.Length(max=250)
    ),
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
    selected = list(dict.fromkeys(msg["regions"]))
    unknown = [key for key in selected if key not in catalog.available]
    if unknown:
        connection.send_error(msg["id"], "invalid_region",
                              "Länderauszug im Geofabrik-Index nicht verfügbar: " + ", ".join(unknown[:3]))
        return
    catalog.settings = {
        "regions": selected, "hour": msg["hour"], "interval_days": msg["interval_days"]
    }
    await catalog.store.async_save(catalog.settings)
    catalog.schedule()
    if selected:
        hass.async_create_task(catalog.async_refresh_all())
    connection.send_result(msg["id"], await hass.async_add_executor_job(catalog.status))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/poi_catalog/refresh",
    vol.Optional("region", default=""): str,
})
@websocket_api.async_response
async def websocket_refresh(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                            msg: dict[str, Any]) -> None:
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Nur Administratoren können den Katalog aktualisieren")
        return
    catalog = manager(hass)
    if not catalog.settings["regions"]:
        connection.send_error(msg["id"], "catalog_disabled", "Zuerst eine Region auswählen")
        return
    region = str(msg.get("region", ""))
    if region and region not in catalog.settings["regions"]:
        connection.send_error(msg["id"], "invalid_region", "Region ist nicht ausgewählt")
        return
    hass.async_create_task(catalog.async_refresh_all(force=True, only=region))
    connection.send_result(msg["id"], await hass.async_add_executor_job(catalog.status))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/poi_catalog/reload_index"})
@websocket_api.async_response
async def websocket_reload_index(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                 msg: dict[str, Any]) -> None:
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Nur Administratoren können die Länderliste aktualisieren")
        return
    catalog = manager(hass)
    await catalog.async_update_index_if_due(force=True)
    connection.send_result(msg["id"], await hass.async_add_executor_job(catalog.status))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/poi_catalog/delete",
    vol.Required("region"): str,
})
@websocket_api.async_response
async def websocket_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                           msg: dict[str, Any]) -> None:
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Nur Administratoren können einen POI-Katalog löschen")
        return
    catalog = manager(hass)
    region = msg["region"]
    if region in catalog.settings["regions"]:
        connection.send_error(msg["id"], "catalog_selected", "Region zuerst abwählen und speichern")
        return
    if catalog.task and not catalog.task.done():
        connection.send_error(msg["id"], "catalog_busy", "Import abwarten, dann erneut löschen")
        return
    try:
        deleted_bytes = await hass.async_add_executor_job(_delete_catalog_file, catalog.directory, region)
    except (ValueError, OSError, sqlite3.Error) as err:
        connection.send_error(msg["id"], "delete_failed", str(err))
        return
    connection.send_result(msg["id"], {
        "deleted_bytes": deleted_bytes,
        "status": await hass.async_add_executor_job(catalog.status),
    })


def async_register_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_status)
    websocket_api.async_register_command(hass, websocket_configure)
    websocket_api.async_register_command(hass, websocket_refresh)
    websocket_api.async_register_command(hass, websocket_reload_index)
    websocket_api.async_register_command(hass, websocket_delete)
