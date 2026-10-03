"""Public OCPDB charging POIs with connector-specific availability and ad-hoc tariffs."""

from __future__ import annotations

import asyncio
import logging
import math
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from . import ocpdb_cache

BASE = "https://api.mobidata-bw.de/ocpdb/api/public/ocpi/3.0"
SOURCES = "https://api.mobidata-bw.de/ocpdb/api/public/v1/sources"
PAGE_SIZE = 1000
MAX_LOCATIONS = 100000
STATUS_FEED_MAX_AGE = 2 * 3600
STATUS_CHANGE_MAX_AGE = 3 * 86400
_STATE = "ocpdb_state"
_LOGGER = logging.getLogger(__name__)


def _timestamp(value: Any) -> float:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def _price(tariff: dict[str, Any]) -> tuple[float | None, bool]:
    """Return an unambiguous EUR/kWh price; unknown/conditional prices stay unknown."""
    if tariff.get("currency") != "EUR":
        return None, False
    prices: list[float] = []
    has_time_fee = False
    for element in tariff.get("elements") or []:
        if not isinstance(element, dict):
            continue
        for component in element.get("price_components") or []:
            if not isinstance(component, dict):
                continue
            kind = component.get("type")
            if kind == "TIME":
                try:
                    has_time_fee |= float(component.get("price") or 0) > 0
                except (TypeError, ValueError):
                    has_time_fee = True
            if kind != "ENERGY":
                continue
            if element.get("restrictions"):
                return None, has_time_fee
            try:
                value = float(component["price"])
                taxes = component.get("taxes") or []
                if len(taxes) > 1 or (taxes and taxes[0].get("name") != "VAT"):
                    return None, has_time_fee
                if taxes:
                    value *= 1 + float(taxes[0]["percentage"]) / 100
                if not math.isfinite(value) or value < 0:
                    return None, has_time_fee
                prices.append(round(value, 4))
            except (KeyError, TypeError, ValueError):
                return None, has_time_fee
    return (prices[0] if prices and len(set(prices)) == 1 else None), has_time_fee


def _connector_key(standard: str) -> str:
    return {"IEC_62196_T2_COMBO": "ccs", "IEC_62196_T2": "type2",
            "CHADEMO": "chademo", "TESLA_S": "tesla"}.get(standard, "")


def _elements(locations: list[dict[str, Any]], tariffs: dict[str, dict[str, Any]],
              associations: dict[str, set[str]], sources: dict[str, dict[str, Any]],
              msg: dict[str, Any], now: float) -> list[dict[str, Any]]:
    """Filter the very same EVSE for plug, power, status and price."""
    result = []
    connector_filter = msg.get("connector_filter", "any")
    min_power = int(msg.get("min_power_kw", 0) or 0)
    only_free = bool(msg.get("only_available", False))
    min_free = max(1, int(msg.get("min_free", 1) or 1))
    price_mode = msg.get("price_mode", "any")
    max_price = float(msg.get("max_price_eur", 0) or 0)
    operators = [str(x).casefold() for x in msg.get("operator_filters", []) if x]
    for loc in locations:
        if not isinstance(loc, dict):
            continue
        coords = loc.get("coordinates") or {}
        try:
            lat, lon = float(coords.get("latitude")), float(coords.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not all(map(math.isfinite, (lat, lon))):
            continue
        operator = str((loc.get("operator") or {}).get("name") or "")
        name = str(loc.get("name") or operator or "Ladestation")
        if operators and not any(x in f"{operator} {name}".casefold() for x in operators):
            continue
        source = str(loc.get("source") or "")
        feed = sources.get(source) or {}
        feed_updated = str(feed.get("realtime_data_updated_at") or "")
        feed_fresh = bool(feed.get("realtime_status") == "ACTIVE" and feed_updated
                          and 0 <= now - _timestamp(feed_updated) <= STATUS_FEED_MAX_AGE)
        matches: list[tuple[dict[str, Any], dict[str, Any], str, float, str, float | None, bool, str]] = []
        for pool in loc.get("charging_pool") or []:
            for evse in pool.get("evses") or []:
                status_updated = str(evse.get("status_last_updated") or "")
                fresh = feed_fresh and status_updated and 0 <= now - _timestamp(status_updated) <= STATUS_CHANGE_MAX_AGE
                status = str(evse.get("status") or "UNKNOWN") if fresh else "UNKNOWN"
                uid = str(evse.get("uid") or "")
                for connector in evse.get("connectors") or []:
                    key = _connector_key(str(connector.get("standard") or ""))
                    if not key or (connector_filter != "any" and key != connector_filter):
                        continue
                    try:
                        power = float(connector.get("max_electric_power") or 0) / 1000
                    except (TypeError, ValueError):
                        continue
                    if not math.isfinite(power) or power < min_power or power <= 0:
                        continue
                    applicable_prices = []
                    for tariff_id in connector.get("tariff_ids") or []:
                        tariff = tariffs.get(str(tariff_id))
                        if not tariff or str(tariff.get("id")) not in associations.get(uid, set()):
                            continue
                        candidate, fee = _price(tariff)
                        applicable_prices.append((candidate, fee, str(tariff.get("last_updated") or "")))
                    # Never label the cheapest among multiple different tariff
                    # associations as a definitive ad-hoc connector price.
                    unambiguous = (len(applicable_prices) == 1
                                   or (applicable_prices and len({x[0] for x in applicable_prices}) == 1))
                    price = applicable_prices[0][0] if unambiguous else None
                    has_time_fee = any(x[1] for x in applicable_prices)
                    price_updated = max((x[2] for x in applicable_prices), default="")
                    if price_mode == "known" and price is None:
                        continue
                    if max_price > 0 and (price is None or price > max_price):
                        continue
                    if only_free and status != "AVAILABLE":
                        continue
                    matches.append((evse, connector, key, power, status, price, has_time_fee, price_updated))
        if not matches:
            continue
        free_uids = {str(x[0].get("uid")) for x in matches if x[4] == "AVAILABLE"}
        if only_free and len(free_uids) < min_free:
            continue
        best = min((x[5] for x in matches if x[5] is not None), default=None)
        keys = {x[2] for x in matches}
        known_status = {x[4] for x in matches}
        tags: dict[str, Any] = {
            "amenity": "charging_station", "name": name, "operator": operator,
            "addr:street": loc.get("address") or "", "addr:postcode": loc.get("postal_code") or "",
            "addr:city": loc.get("city") or "", "addr:country": loc.get("country") or "",
            "driveloom:provider": "ocpdb", "driveloom:data_provider": source,
            "driveloom:availability": "available" if free_uids else (
                "occupied" if known_status and "UNKNOWN" not in known_status else "unknown"),
            "driveloom:free_count": len(free_uids),
            "driveloom:total_count": len({str(x[0].get('uid')) for x in matches}),
            "driveloom:status_updated": max((str(x[0].get("status_last_updated") or "") for x in matches), default=""),
            "driveloom:feed_updated": feed_updated,
            "driveloom:price_eur_kwh": best,
            "driveloom:price_updated": max((x[7] for x in matches if x[5] == best), default="") if best is not None else "",
            "driveloom:time_fee": any(x[6] for x in matches if x[5] == best),
            "driveloom:power_kw": max(x[3] for x in matches),
        }
        for key in keys:
            socket = {"ccs": "socket:type2_combo", "type2": "socket:type2",
                      "chademo": "socket:chademo", "tesla": "socket:tesla_supercharger"}[key]
            tagged = [x for x in matches if x[2] == key]
            tags[socket] = str(len({str(x[0].get("uid")) for x in tagged}))
            tags[f"{socket}:output"] = f"{max(x[3] for x in tagged):g} kW"
        result.append({"type": "ocpdb", "id": str(loc.get("id")), "lat": lat, "lon": lon,
                       "tags": tags, "provider": "ocpdb", "sources": "ocpdb"})
    return result


async def async_get_pois(hass: Any, msg: dict[str, Any]) -> dict[str, Any]:
    """Page through German locations and reuse complete SQLite snapshots."""
    state = hass.data.setdefault(DOMAIN, {}).setdefault(_STATE, {"lock": asyncio.Lock(), "cache": {}})
    key = (round(float(msg["latitude"]), 3), round(float(msg["longitude"]), 3), int(msg["radius_km"]),
           msg.get("connector_filter"), msg.get("min_power_kw"), msg.get("only_available"),
           msg.get("min_free"), msg.get("price_mode"), msg.get("max_price_eur"),
           tuple(msg.get("operator_filters") or []))
    async with state["lock"]:
        cached = state["cache"].get(key)
        if cached and not msg.get("force_refresh") and time.monotonic() - cached[0] < 90:
            return cached[1]
        snapshot_key = ":".join((str(round(float(msg["latitude"]), 3)),
                                 str(round(float(msg["longitude"]), 3)), str(int(msg["radius_km"])), "DEU"))
        path = Path(hass.config.path(".storage", ocpdb_cache.DB_FILENAME))
        snapshot = await hass.async_add_executor_job(ocpdb_cache.read, path, snapshot_key)
        now = time.time()
        max_cache_age = 90 if msg.get("only_available") else 900
        use_snapshot = bool(snapshot and not msg.get("force_refresh")
                            and 0 <= now - snapshot[0] < max_cache_age)
        session = async_get_clientsession(hass)

        async def fetch(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=28),
                                   headers={"Accept": "application/json", "User-Agent": "DriveLoom/0.2.0b10"}) as response:
                if response.status != 200:
                    raise ValueError(f"OCPDB: HTTP {response.status}")
                if response.content_length and response.content_length > 20_000_000:
                    raise ValueError("OCPDB: Antwort zu groß")
                raw = await response.read()
                if len(raw) > 20_000_000:
                    raise ValueError("OCPDB: Antwort zu groß")
                data = await response.json(content_type=None)
                if not isinstance(data, dict):
                    raise ValueError("OCPDB: ungültige Antwort")
                return data

        truncated = False
        warning = ""
        if use_snapshot:
            data = snapshot[1]
            locations = data["locations"]
            tariffs = data["tariffs"]
            associations = {uid: set(ids) for uid, ids in data["associations"].items()}
            sources = data["sources"]
            total = data["total"]
            age = int(now - snapshot[0])
            if age >= 90:
                sources = {uid: {**info, "realtime_status": "UNKNOWN"} for uid, info in sources.items()}
            if age >= 60:
                warning = f"OCPDB-Zwischenspeicher: Daten vor {age // 60} Minuten abgerufen."
        else:
          try:
           async with asyncio.timeout(120):
            if not state.get("tariffs") or now - state.get("tariffs_at", 0) > 1800:
                tariffs: dict[str, dict[str, Any]] = {}
                associations: dict[str, set[str]] = {}
                for endpoint in ("tariffs", "tariff-associations"):
                    offset = 0
                    while True:
                        data = await fetch(f"{BASE}/{endpoint}", {"limit": PAGE_SIZE, "offset": offset})
                        for item in data.get("items") or []:
                            if endpoint == "tariffs":
                                tariffs[str(item.get("original_id"))] = item
                            elif item.get("audience") == "AD_HOC_PAYMENT":
                                for evse in item.get("evses") or []:
                                    associations.setdefault(str(evse.get("evse_uid")), set()).add(str(item.get("tariff_id")))
                        offset += len(data.get("items") or [])
                        if offset >= int(data.get("total_count") or 0) or not data.get("items"):
                            break
                state.update(tariffs=tariffs, associations=associations, tariffs_at=now)
            if not state.get("sources") or now - state.get("sources_at", 0) > 300:
                payload = await fetch(SOURCES)
                state.update(sources={x["uid"]: x for x in payload.get("items") or [] if x.get("uid")}, sources_at=now)
            locations = []
            total = 0
            offset = 0
            params = {"lat": msg["latitude"], "lon": msg["longitude"],
                      "radius": int(msg["radius_km"]) * 1000, "country": "DEU", "limit": PAGE_SIZE}
            active_sources = [uid for uid, info in state["sources"].items()
                              if info.get("realtime_data_updated_at") and uid != "bnetza_api"]
            if active_sources:
                params["source_uids"] = ",".join(active_sources)
            while offset < MAX_LOCATIONS:
                data = await fetch(f"{BASE}/locations", {**params, "offset": offset})
                page = data.get("items") or []
                locations.extend(page)
                total = int(data.get("total_count") or 0)
                offset += len(page)
                if offset >= total or not page:
                    break
            truncated = offset < total
            if not truncated:
                await hass.async_add_executor_job(ocpdb_cache.write, path, snapshot_key, time.time(), {
                    "locations": locations, "tariffs": state["tariffs"],
                    "associations": {uid: list(ids) for uid, ids in state["associations"].items()},
                    "sources": state["sources"], "total": total,
                })
            tariffs, associations, sources = state["tariffs"], state["associations"], state["sources"]
            warning = f"OCPDB: {total} Kandidaten, nur erste {offset} geprüft; Suchweite verkleinern." if truncated else ""
          except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, OSError, sqlite3.Error) as err:
            if not snapshot:
                raise
            _LOGGER.warning("OCPDB request failed, using cached locations: %s", err)
            data = snapshot[1]
            locations, tariffs = data["locations"], data["tariffs"]
            associations = {uid: set(ids) for uid, ids in data["associations"].items()}
            sources, total = data["sources"], data["total"]
            warning = "OCPDB nicht erreichbar: gespeicherte Standorte und Preise; Belegung unbekannt."
            sources = {uid: {**info, "realtime_status": "UNKNOWN"} for uid, info in sources.items()}
        elements = _elements(locations, tariffs, associations, sources, msg, time.time())
        center_lat, center_lon = float(msg["latitude"]), float(msg["longitude"])
        elements.sort(key=lambda item: (item["lat"] - center_lat) ** 2
                      + ((item["lon"] - center_lon) * math.cos(math.radians(center_lat))) ** 2)
        result = {"elements": elements[:int(msg.get("max_results", 500))], "endpoint": BASE,
                  "sources": ["OCPDB · MobiData BW"], "warnings": [warning] if warning else [],
                  "charging_status": "ready", "candidate_limit_hit": truncated,
                  "candidate_limit": MAX_LOCATIONS if truncated else total, "catalog": False}
        state["cache"] = {key: (time.monotonic(), result)}
        return result
