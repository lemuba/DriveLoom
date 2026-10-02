"""Manual, source-aware search ahead. No background requests or paid fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .db import SQLiteStore

_LOGGER = logging.getLogger(__name__)
_STORE_KEY = f"{DOMAIN}.smart_search"
_MODEL = "gemini-2.5-flash-lite"
_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent"
_PROFILE = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1, max=70)),
    vol.Required("query"): vol.All(str, vol.Length(min=3, max=350)),
    vol.Optional("kind", default="charging"): vol.In(("charging", "place", "event")),
    vol.Optional("radius_km", default=100): vol.In((10, 25, 50, 100, 150, 200)),
    vol.Optional("min_power_kw", default=100): vol.In((0, 50, 100, 150, 200, 300)),
    vol.Optional("max_price_eur", default=0): vol.All(vol.Coerce(float), vol.Range(min=0, max=3)),
    vol.Optional("criteria", default=""): vol.All(str, vol.Length(max=350)),
    vol.Optional("date", default=""): vol.All(str, vol.Length(max=10)),
}, extra=vol.PREVENT_EXTRA)
_DEFAULT = {"name": "Günstige Schnelllader", "query": "Ad-hoc-CCS-Schnelllader",
            "kind": "charging", "radius_km": 100, "min_power_kw": 100,
            "max_price_eur": 0.59, "criteria": "", "date": ""}
_LOCK = "smart_search_lock"
_BUSY = "smart_search_busy"
_LAST = "smart_search_last"


def _store(hass: HomeAssistant) -> SQLiteStore:
    return SQLiteStore(hass, _STORE_KEY)


def _lock(hass: HomeAssistant) -> asyncio.Lock:
    return hass.data.setdefault(DOMAIN, {}).setdefault(_LOCK, asyncio.Lock())


async def _read(hass: HomeAssistant) -> dict[str, Any]:
    data = await _store(hass).async_load() or {}
    return data if isinstance(data, dict) else {}


def _safe_url(value: Any) -> str:
    url = str(value or "").strip()[:1500]
    parsed = urlparse(url)
    return url if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password else ""


def _distance_km(a: float, b: float, c: float, d: float) -> float:
    p, q = math.radians(c - a), math.radians(d - b)
    v = math.sin(p / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(q / 2) ** 2
    return 12742 * math.asin(min(1, math.sqrt(v)))


def _bearing(a: float, b: float, c: float, d: float) -> float:
    dy = math.sin(math.radians(d - b)) * math.cos(math.radians(c))
    dx = math.cos(math.radians(a)) * math.sin(math.radians(c)) - math.sin(math.radians(a)) * math.cos(math.radians(c)) * math.cos(math.radians(d - b))
    return (math.degrees(math.atan2(dy, dx)) + 360) % 360


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Die Suchantwort enthält kein lesbares JSON") from None
        value = json.loads(text[start:end + 1])
    if not isinstance(value, dict) or not isinstance(value.get("places"), list):
        raise ValueError("Die Suchantwort enthält keine Ortsliste")
    return value


def _normalise(raw: list[Any], sources: list[str], lat: float, lon: float,
               heading: float | None, profile: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for item in raw[:35]:
        if not isinstance(item, dict):
            continue
        try:
            p, q = float(item.get("lat")), float(item.get("lon"))
        except (TypeError, ValueError):
            continue
        if not all(map(math.isfinite, (p, q))) or abs(p) > 90 or abs(q) > 180:
            continue
        distance = _distance_km(lat, lon, p, q)
        if distance < 0.1 or distance > profile["radius_km"]:
            continue
        if heading is not None and abs((_bearing(lat, lon, p, q) - heading + 540) % 360 - 180) > 75:
            continue
        ident = (round(p * 10000), round(q * 10000))
        if ident in seen:
            continue
        seen.add(ident)
        source = _safe_url(item.get("source_url"))
        # Search results must contain at least one actual grounding source. A
        # model-provided link by itself is never evidence of a checked price.
        if not sources or not source:
            continue
        source_attested = source in sources
        power = item.get("power_kw")
        try:
            power = float(power) if power is not None else None
        except (ValueError, TypeError):
            power = None
        if power is not None and (not math.isfinite(power) or power < 0 or power > 2000):
            power = None
        if profile["kind"] == "charging" and profile["min_power_kw"]:
            if power is None or power < profile["min_power_kw"]:
                continue
        price = item.get("price_eur_kwh")
        try:
            price = float(price) if price is not None else None
        except (ValueError, TypeError):
            price = None
        if price is not None and (not math.isfinite(price) or price <= 0 or price > 5):
            price = None
        if profile["kind"] == "charging" and profile["max_price_eur"] and price is not None and price > profile["max_price_eur"]:
            continue
        name = str(item.get("name") or "").strip()[:120]
        if not name:
            continue
        # Results are leads with source links, never a verified current tariff.
        result.append({"id": f"smart:{len(result)}:{ident[0]}:{ident[1]}",
                       "name": name, "lat": p, "lon": q,
                       "address": str(item.get("address") or "")[:180],
                       "power_kw": power, "price_eur_kwh": price,
                       "price_status": "unverified" if price is not None else "unknown",
                       "source_url": source, "source_attested": source_attested,
                       "note": str(item.get("note") or "")[:240],
                       "distance_km": round(distance, 1)})
    result.sort(key=lambda place: place["distance_km"])
    return result[:12]


async def _search(hass: HomeAssistant, key: str, profile: dict[str, Any],
                  lat: float, lon: float, heading: float | None) -> dict[str, Any]:
    direction = f"Kompassrichtung {round(heading)} Grad (grober Suchkorridor)" if heading is not None else "alle Richtungen"
    request = (f"Suche jetzt reale Orte; Datum UTC {datetime.now(timezone.utc).date()}. "
               f"Startpunkt {lat:.5f},{lon:.5f}; {direction}; maximal {profile['radius_km']} km Luftlinie. "
               f"Art {profile['kind']}; Wunsch: {profile['query']}. Kriterien: {profile['criteria'] or 'keine'}. "
               f"Datum: {profile['date'] or 'jetzt'}. "
               f"Bei Ladestationen nur CCS und nachweisbar >= {profile['min_power_kw']} kW; "
               f"bevorzugter Ad-hoc-Preis <= {profile['max_price_eur']} EUR/kWh (0 = beliebig). "
               "Suche im Web nach konkreten Quellen. Keine Orte oder Koordinaten erfinden. "
               "Nur einen Preis nennen, wenn er ausdrücklich für Ad-hoc-Laden gilt; sonst null. "
               "Antworte ausschließlich als JSON mit places: Array aus name, lat, lon, address, "
               "power_kw (Zahl/null), price_eur_kwh (Zahl/null), source_url (https), note. "
               "Höchstens 12 Orte; [] falls nicht belegbar. Keine Markdown-Zäune.")
    timeout = aiohttp.ClientTimeout(total=65)
    async with async_get_clientsession(hass).post(
        _ENDPOINT, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": request}]}],
              "tools": [{"google_search": {}}],
              "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2800}},
        timeout=timeout,
    ) as response:
        if response.status == 429:
            raise ValueError("Kostenloses API-Limit erreicht. Bitte später erneut versuchen.")
        if response.status in (401, 403):
            raise ValueError("Gemini-Schlüssel abgelehnt oder kostenlose Websuche nicht verfügbar.")
        if response.status != 200:
            _LOGGER.warning("DriveLoom search provider HTTP %s", response.status)
            raise ValueError(f"Suchdienst derzeit nicht verfügbar (HTTP {response.status})")
        payload = await response.json(content_type=None)
    candidate = (payload.get("candidates") or [{}])[0]
    grounding = candidate.get("groundingMetadata") or {}
    sources = list(dict.fromkeys(url for chunk in grounding.get("groundingChunks", [])
                                  if isinstance(chunk, dict)
                                  for url in [_safe_url((chunk.get("web") or {}).get("uri"))] if url))[:25]
    if not sources:
        raise ValueError("Keine Webquellen zurückgegeben; deshalb keine POIs übernommen.")
    content = "".join(part.get("text", "") for part in (candidate.get("content") or {}).get("parts", [])
                      if isinstance(part, dict))
    places = _normalise(_extract_json(content).get("places", []), sources, lat, lon, heading, profile)
    return {"places": places, "sources": sources, "model": _MODEL,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "warning": "KI-Suchtreffer: Koordinaten, Leistung und Ad-hoc-Preis vor Anfahrt an der Quelle prüfen; Entfernung ist Luftlinie."}


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/list"})
@websocket_api.async_response
async def websocket_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    data = await _read(hass)
    connection.send_result(msg["id"], {"profiles": data.get("profiles") or {"starter": _DEFAULT},
                                        "configured": bool(data.get("api_key")), "model": _MODEL})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/configure",
                                  vol.Required("api_key"): vol.All(str, vol.Length(max=250))})
@websocket_api.async_response
async def websocket_configure(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Nur Administratoren können den API-Schlüssel speichern")
        return
    key = msg["api_key"].strip()
    async with _lock(hass):
        data = await _read(hass)
        if key:
            data["api_key"] = key
        else:
            data.pop("api_key", None)
        await _store(hass).async_save(data)
    connection.send_result(msg["id"], {"configured": bool(key)})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/save",
                                  vol.Required("key"): vol.All(str, vol.Match(r"^[a-z0-9_-]{1,60}$")),
                                  vol.Required("profile"): dict})
@websocket_api.async_response
async def websocket_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        profile = _PROFILE(msg["profile"])
    except vol.Invalid as err:
        connection.send_error(msg["id"], "invalid_profile", str(err))
        return
    if not math.isfinite(profile["max_price_eur"]):
        connection.send_error(msg["id"], "invalid_profile", "Preis muss eine endliche Zahl sein")
        return
    async with _lock(hass):
        data = await _read(hass)
        profiles = data.setdefault("profiles", {"starter": _DEFAULT.copy()})
        if len(profiles) >= 30 and msg["key"] not in profiles:
            connection.send_error(msg["id"], "too_many_profiles", "Maximal 30 Suchvorlagen")
            return
        profiles[msg["key"]] = profile
        await _store(hass).async_save(data)
    connection.send_result(msg["id"], {"profiles": profiles})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/delete",
                                  vol.Required("key"): vol.All(str, vol.Match(r"^[a-z0-9_-]{1,60}$"))})
@websocket_api.async_response
async def websocket_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    async with _lock(hass):
        data = await _read(hass)
        profiles = data.setdefault("profiles", {"starter": _DEFAULT.copy()})
        profiles.pop(msg["key"], None)
        await _store(hass).async_save(data)
    connection.send_result(msg["id"], {"profiles": profiles})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smart_search/run",
                                  vol.Required("profile"): dict,
                                  vol.Required("latitude"): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
                                  vol.Required("longitude"): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
                                  vol.Optional("bearing"): vol.All(vol.Coerce(float), vol.Range(min=0, max=360))})
@websocket_api.async_response
async def websocket_run(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    try:
        profile = _PROFILE(msg["profile"])
    except vol.Invalid as err:
        connection.send_error(msg["id"], "invalid_profile", str(err))
        return
    if not math.isfinite(profile["max_price_eur"]) or not all(
        math.isfinite(msg[field]) for field in ("latitude", "longitude")
    ) or ("bearing" in msg and not math.isfinite(msg["bearing"])):
        connection.send_error(msg["id"], "invalid_request", "Koordinaten oder Preis ungültig")
        return
    state = hass.data.setdefault(DOMAIN, {})
    key = (await _read(hass)).get("api_key")
    if not key:
        connection.send_error(msg["id"], "not_configured", "Gemini-API-Schlüssel fehlt")
        return
    now = time.monotonic()
    if state.get(_BUSY):
        connection.send_error(msg["id"], "busy", "Eine Suche läuft bereits")
        return
    if now - state.get(_LAST, 0) < 15:
        connection.send_error(msg["id"], "rate_limited", "Bitte 15 Sekunden bis zur nächsten Suche warten")
        return
    state[_BUSY] = True
    state[_LAST] = now
    try:
        result = await _search(hass, key, profile, msg["latitude"], msg["longitude"], msg.get("bearing"))
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, json.JSONDecodeError) as err:
        connection.send_error(msg["id"], "search_failed", str(err))
    except Exception:
        _LOGGER.exception("DriveLoom manual search failed")
        connection.send_error(msg["id"], "search_failed", "Suche fehlgeschlagen; Details im HA-Protokoll")
    else:
        connection.send_result(msg["id"], result)
    finally:
        state[_BUSY] = False


def async_register_websocket(hass: HomeAssistant) -> None:
    for handler in (websocket_list, websocket_configure, websocket_save, websocket_delete, websocket_run):
        websocket_api.async_register_command(hass, handler)
