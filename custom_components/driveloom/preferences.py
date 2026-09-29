"""Persist map UI preferences in the same database as vehicle analytics."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .db import SQLiteStore


WS_GET = f"{DOMAIN}/preferences/get"
WS_SET = f"{DOMAIN}/preferences/set"
PREFERENCE_KEY = vol.All(str, vol.Length(min=1, max=100))


def _store(hass: HomeAssistant, connection: websocket_api.ActiveConnection, key: str) -> SQLiteStore:
    return SQLiteStore(hass, f"map_preferences:{connection.user.id}:{key}")


@websocket_api.websocket_command(
    {vol.Required("type"): WS_GET, vol.Required("key"): PREFERENCE_KEY}
)
@websocket_api.async_response
async def websocket_get(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    preferences = await _store(hass, connection, msg["key"]).async_load()
    connection.send_result(msg["id"], {"preferences": preferences or {}})


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_SET,
        vol.Required("key"): PREFERENCE_KEY,
        vol.Required("preferences"): dict,
    }
)
@websocket_api.async_response
async def websocket_set(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    preferences = dict(msg["preferences"])
    if len(str(preferences)) > 100_000:
        connection.send_error(msg["id"], "preferences_too_large", "Map preferences exceed limit")
        return
    await _store(hass, connection, msg["key"]).async_save(preferences)
    connection.send_result(msg["id"], {"saved": True})


def async_register_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_get)
    websocket_api.async_register_command(hass, websocket_set)
