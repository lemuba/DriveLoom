"""Offline contract checks for the grounded, manual search response."""
import ast
import asyncio
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
tree = ast.parse((root / "custom_components/driveloom/smart_search.py").read_text())
names = {"_safe_url", "_distance_km", "_bearing", "_extract_json", "_normalise", "_search"}
selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in names]
ns = {"Any": object, "math": math, "json": json, "urlparse": urlparse,
      "datetime": datetime, "timezone": timezone,
      "HomeAssistant": object,
      "_MODEL": "gemini-2.5-flash-lite", "_ENDPOINT": "https://example.org:generateContent"}
exec(compile(ast.Module(body=selected, type_ignores=[]), "<smart-production>", "exec"), ns)
profile = {"query":"Ad-hoc-CCS-Schnelllader", "criteria":"", "kind":"charging", "date":"",
           "radius_km":100, "min_power_kw":100, "max_price_eur":0.59}
raw = [
    {"name":"Voraus", "lat":53.9,"lon":9.8,"power_kw":150,"price_eur_kwh":0.49,
     "source_url":"https://example.org/price"},
    {"name":"Teuer", "lat":53.95,"lon":9.75,"power_kw":150,"price_eur_kwh":0.79,
     "source_url":"https://example.org/price"},
    {"name":"Hinter", "lat":53.8,"lon":9.7,"power_kw":150,"price_eur_kwh":0.45,
     "source_url":"https://example.org/price"},
    {"name":"Ohne Quelle", "lat":53.98,"lon":9.8,"power_kw":150,"price_eur_kwh":0.45},
]
assert not ns["_normalise"](raw, [], 53.8, 9.8, 0, profile)
places = ns["_normalise"](raw, ["https://example.org/price"], 53.8, 9.8, 0, profile)
assert len(places) == 1 and places[0]["name"] == "Voraus"
assert places[0]["price_status"] == "unverified" and places[0]["source_attested"]
assert not ns["_safe_url"]("javascript:alert(1)")
assert ns["_extract_json"]("```json\n{\"places\": []}\n```") == {"places": []}

class Response:
    status = 200
    async def __aenter__(self): return self
    async def __aexit__(self, *_): pass
    async def json(self, **_):
        return {"candidates": [{"groundingMetadata": {"groundingChunks": [
            {"web": {"uri": "https://example.org/price"}}]},
            "content": {"parts": [{"text": json.dumps({"places": raw})}]}}]}

class Session:
    def post(self, url, *, headers, json, timeout):
        assert url.endswith(":generateContent") and headers["x-goog-api-key"] == "fake"
        assert json["tools"] == [{"google_search": {}}]
        assert "53.80000,9.80000" in json["contents"][0]["parts"][0]["text"]
        return Response()

ns["aiohttp"] = SimpleNamespace(ClientTimeout=lambda **_: None)
ns["async_get_clientsession"] = lambda _: Session()
result = asyncio.run(ns["_search"](object(), "fake", profile, 53.8, 9.8, 0))
assert [item["name"] for item in result["places"]] == ["Voraus"]
assert result["sources"] == ["https://example.org/price"]

class NoGrounding(Response):
    async def json(self, **_): return {"candidates": [{"content": {"parts": [{"text": "{\"places\": []}"}]}}]}

class NoGroundingSession(Session):
    def post(self, *_, **__): return NoGrounding()

ns["async_get_clientsession"] = lambda _: NoGroundingSession()
try:
    asyncio.run(ns["_search"](object(), "fake", profile, 53.8, 9.8, 0))
    raise AssertionError("Ungrounded search must fail")
except ValueError as err:
    assert "Webquellen" in str(err)

# The key stays in HA's store; list responses expose only a configured flag.
handlers = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
            and node.name in {"websocket_list", "websocket_configure"}]
for handler in handlers:
    handler.decorator_list = []
state = {}
class Store:
    async def async_load(self): return state.copy()
    async def async_save(self, value): state.clear(); state.update(value)

ns.update({"_read": lambda hass: Store().async_load(), "_store": lambda hass: Store(),
           "_lock": lambda hass: asyncio.Lock(),
           "websocket_api": SimpleNamespace(ActiveConnection=object),
           "_DEFAULT": {"name": "Standard"}})
exec(compile(ast.Module(body=handlers, type_ignores=[]), "<smart-handlers>", "exec"), ns)
class Connection:
    def __init__(self, admin): self.user=SimpleNamespace(is_admin=admin);self.result=None;self.error=None
    def send_result(self, _, result): self.result=result
    def send_error(self, _, code, detail): self.error=(code, detail)

admin, guest = Connection(True), Connection(False)
asyncio.run(ns["websocket_configure"](object(), guest, {"id":1,"api_key":"private"}))
assert guest.error[0] == "unauthorized" and not state
asyncio.run(ns["websocket_configure"](object(), admin, {"id":2,"api_key":"private"}))
asyncio.run(ns["websocket_list"](object(), guest, {"id":3}))
assert guest.result["configured"] and "private" not in repr(guest.result)
print("PASS manual grounded search validates sources, direction, power and price")
