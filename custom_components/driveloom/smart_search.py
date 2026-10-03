"""Manual charging search through public OCPDB data, without AI or API secrets."""

from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .db import SQLiteStore
from .ocpdb import BASE, async_get_pois

_LOGGER = logging.getLogger(__name__)
_STORE_KEY = f"{DOMAIN}.smart_search"
_LOCK = "smart_search_lock"
_BUSY = "smart_search_busy"
_LAST = "smart_search_last"
_PROFILE = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1, max=70)),
    vol.Required("query"): vol.All(str, vol.Length(min=3, max=350)),
    vol.Optional("kind", default="charging"): vol.In(("charging",)),
    vol.Optional("radius_km", default=100): vol.In((10, 25, 50, 100, 150, 200)),
    vol.Optional("min_power_kw", default=100): vol.In((0, 50, 100, 150, 200, 300)),
    vol.Optional("max_price_eur", default=0): vol.All(vol.Coerce(float), vol.Range(min=0, max=3)),
    vol.Optional("price_mode", default="any"): vol.In(("any", "known", "max")),
    vol.Optional("only_available", default=False): bool,
    vol.Optional("criteria", default=""): vol.All(str, vol.Length(max=350)),
    vol.Optional("date", default=""): vol.All(str, vol.Length(max=10)),
}, extra=vol.PREVENT_EXTRA)
_DEFAULT = {"name": "Schnelllader voraus", "query": "CCS-Schnelllader", "kind": "charging",
            "radius_km": 100, "min_power_kw": 100, "max_price_eur": 0.59,
            "price_mode": "any", "only_available": False, "criteria": "", "date": ""}


def _store(hass: HomeAssistant) -> SQLiteStore:
    return SQLiteStore(hass, _STORE_KEY)


def _lock(hass: HomeAssistant) -> asyncio.Lock:
    return hass.data.setdefault(DOMAIN, {}).setdefault(_LOCK, asyncio.Lock())


async def _read(hass: HomeAssistant) -> dict[str, Any]:
    data = await _store(hass).async_load() or {}
    return data if isinstance(data, dict) else {}


async def async_remove_legacy_ai_keys(hass: HomeAssistant) -> None:
    """Delete old Google AI Studio and Tavily keys, including usage metadata."""
    async with _lock(hass):
        data = await _read(hass)
        cleaned = {k: v for k, v in data.items() if k not in ("api_key", "gemini_key", "tavily_key", "tavily_usage")}
        if cleaned != data:
            await _store(hass).async_save(cleaned)


def _distance_km(a: float, b: float, c: float, d: float) -> float:
    p, q = math.radians(c - a), math.radians(d - b)
    v = math.sin(p / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(q / 2) ** 2
    return 12742 * math.asin(min(1, math.sqrt(v)))


def _bearing(a: float, b: float, c: float, d: float) -> float:
    dy = math.sin(math.radians(d - b)) * math.cos(math.radians(c))
    dx = math.cos(math.radians(a)) * math.sin(math.radians(c)) - math.sin(math.radians(a)) * math.cos(math.radians(c)) * math.cos(math.radians(d - b))
    return (math.degrees(math.atan2(dy, dx)) + 360) % 360


async def _local_charging(hass: HomeAssistant, profile: dict[str, Any], lat: float,
                          lon: float, heading: float | None, limit: int = 12) -> dict[str, Any]:
    result = await async_get_pois(hass, {
        "latitude": lat, "longitude": lon, "radius_km": profile["radius_km"],
        "connector_filter": "ccs", "min_power_kw": profile["min_power_kw"],
        "only_available": profile.get("only_available", False),
        "price_mode": "known" if profile.get("price_mode") in ("known", "max") else "any",
        "max_price_eur": profile["max_price_eur"] if profile.get("price_mode") == "max" else 0,
        "max_results": 3000,
    })
    places = []
    for element in result["elements"]:
        tags = element["tags"]
        p, q = element["lat"], element["lon"]
        distance = _distance_km(lat, lon, p, q)
        if distance < 0.1 or (heading is not None and abs((_bearing(lat, lon, p, q) - heading + 540) % 360 - 180) > 75):
            continue
        places.append({
            "id": f"smart:ocpdb:{element['id']}", "name": tags["name"], "lat": p, "lon": q,
            "address": ", ".join(str(tags.get(k)) for k in ("addr:street", "addr:postcode", "addr:city") if tags.get(k)),
            "operator": tags.get("operator"), "power_kw": tags.get("driveloom:power_kw"),
            "price_eur_kwh": tags.get("driveloom:price_eur_kwh"),
            "price_status": "ad_hoc" if tags.get("driveloom:price_eur_kwh") is not None else "unknown",
            "free_count": tags.get("driveloom:free_count"), "status_updated": tags.get("driveloom:status_updated"),
            "time_fee": tags.get("driveloom:time_fee"), "distance_km": round(distance, 1),
            "source_url": f"{BASE}/locations/{element['id']}", "source_attested": True,
            "note": "OCPDB · Ad-hoc-Tarif und Belegung mit Quellenzeitpunkt prüfen.",
        })
    places.sort(key=lambda item: item["distance_km"])
    return {"places": places[:limit], "sources": [], "model": "ocpdb",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "warning": "Status und Preise können sich ändern. " + " ".join(result.get("warnings") or [])}


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/list"})
@websocket_api.async_response
async def websocket_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    data = await _read(hass)
    profiles = {key: value for key, value in (data.get("profiles") or {}).items()
                if isinstance(value, dict) and value.get("kind", "charging") == "charging"}
    connection.send_result(msg["id"], {"profiles": profiles or {"starter": _DEFAULT}, "model": "ocpdb"})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/save",
                                  vol.Required("key"): vol.All(str, vol.Match(r"^[a-z0-9_-]{1,60}$")),
                                  vol.Required("profile"): dict})
@websocket_api.async_response
async def websocket_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        profile = _PROFILE(msg["profile"])
        if not math.isfinite(profile["max_price_eur"]):
            raise ValueError("Preis muss eine endliche Zahl sein")
        if profile["price_mode"] == "max" and profile["max_price_eur"] <= 0:
            raise ValueError("Für den Höchstpreis einen Betrag größer null eingeben")
    except (vol.Invalid, ValueError) as err:
        connection.send_error(msg["id"], "invalid_profile", str(err))
        return
    async with _lock(hass):
        data = await _read(hass)
        profiles = data.setdefault("profiles", {})
        active = sum(isinstance(value, dict) and value.get("kind", "charging") == "charging"
                     for value in profiles.values())
        if active >= 30 and msg["key"] not in profiles:
            connection.send_error(msg["id"], "too_many_profiles", "Maximal 30 Suchvorlagen")
            return
        profiles[msg["key"]] = profile
        await _store(hass).async_save(data)
    connection.send_result(msg["id"], {"profiles": {k: v for k, v in profiles.items() if v.get("kind", "charging") == "charging"}})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/delete",
                                  vol.Required("key"): vol.All(str, vol.Match(r"^[a-z0-9_-]{1,60}$"))})
@websocket_api.async_response
async def websocket_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    async with _lock(hass):
        data = await _read(hass)
        profiles = data.setdefault("profiles", {})
        profiles.pop(msg["key"], None)
        await _store(hass).async_save(data)
    connection.send_result(msg["id"], {"profiles": {k: v for k, v in profiles.items() if v.get("kind", "charging") == "charging"}})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/run",
                                  vol.Required("profile"): dict,
                                  vol.Required("latitude"): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
                                  vol.Required("longitude"): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
                                  vol.Optional("local_only", default=False): bool,
                                  vol.Optional("bearing"): vol.All(vol.Coerce(float), vol.Range(min=0, max=360))})
@websocket_api.async_response
async def websocket_run(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        profile = _PROFILE(msg["profile"])
        if not math.isfinite(profile["max_price_eur"]) or not all(math.isfinite(msg[k]) for k in ("latitude", "longitude")):
            raise ValueError("Koordinaten oder Preis ungültig")
        if profile["price_mode"] == "max" and profile["max_price_eur"] <= 0:
            raise ValueError("Für den Höchstpreis einen Betrag größer null eingeben")
    except (vol.Invalid, ValueError) as err:
        connection.send_error(msg["id"], "invalid_request", str(err))
        return
    state = hass.data.setdefault(DOMAIN, {})
    now = time.monotonic()
    if state.get(_BUSY):
        connection.send_error(msg["id"], "busy", "Eine Suche läuft bereits")
        return
    if now - state.get(_LAST, 0) < 15:
        connection.send_error(msg["id"], "rate_limited", "Bitte 15 Sekunden bis zur nächsten Suche warten")
        return
    state[_BUSY], state[_LAST] = True, now
    try:
        result = await _local_charging(hass, profile, msg["latitude"], msg["longitude"], msg.get("bearing"))
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
        connection.send_error(msg["id"], "search_failed", str(err))
    except Exception:
        _LOGGER.exception("DriveLoom charger search failed")
        connection.send_error(msg["id"], "search_failed", "Suche fehlgeschlagen; Details im HA-Protokoll")
    else:
        connection.send_result(msg["id"], result)
    finally:
        state[_BUSY] = False


def async_register_websocket(hass: HomeAssistant) -> None:
    for handler in (websocket_list, websocket_save, websocket_delete, websocket_run):
        websocket_api.async_register_command(hass, handler)
