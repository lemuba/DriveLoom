"""Offline check for explicit Photon lookup, result validation and cache."""
import ast
import asyncio
import copy
import math
import time
from pathlib import Path
from urllib.parse import urlencode

root = Path(__file__).resolve().parents[1]
tree = ast.parse((root / "custom_components/driveloom/travel.py").read_text())
handler = copy.deepcopy(next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                             and node.name == "websocket_search"))
handler.decorator_list = []

class Response:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    def raise_for_status(self):
        pass

    async def json(self, **_):
        return {"features": [
            {"geometry": {"coordinates": [24.753, 59.437]},
             "properties": {"name": "Tallinn", "country": "Estland"}},
            {"geometry": {"coordinates": [201, 59]}, "properties": {"name": "Ungültig"}},
        ]}

class Session:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response()

session = Session()
ns = {"HomeAssistant": object, "websocket_api": type("WS", (), {"ActiveConnection": object}),
      "Any": object, "asyncio": asyncio, "time": time, "math": math,
      "urlencode": urlencode, "DOMAIN": "driveloom", "SEARCH_KEY": "travel_search",
      "PHOTON_URL": "https://photon.komoot.io/api/", "ClientError": Exception,
      "async_get_clientsession": lambda _: session}
exec(compile(ast.Module(body=[handler], type_ignores=[]), "<travel-search>", "exec"), ns)

class Connection:
    def __init__(self):
        self.results = []
        self.errors = []

    def send_result(self, msg_id, result):
        self.results.append((msg_id, result))

    def send_error(self, msg_id, code, message):
        self.errors.append((msg_id, code, message))

async def run():
    hass = type("Hass", (), {"data": {}})()
    connection = Connection()
    search = ns["websocket_search"]
    await search(hass, connection, {"id": 1, "query": "  "})
    assert connection.errors[0][1] == "travel_search_failed" and not session.calls
    await search(hass, connection, {"id": 2, "query": "Tallinn"})
    assert len(session.calls) == 1 and "q=Tallinn" in session.calls[0][0]
    assert connection.results[-1][1]["results"] == [{"name": "Tallinn", "address": "Estland",
                                                   "lat": 59.437, "lon": 24.753}]
    await search(hass, connection, {"id": 3, "query": "TALLINN"})
    assert len(session.calls) == 1 and len(connection.results) == 2

asyncio.run(run())
print("PASS explicit travel search, invalid result rejection and cache")
