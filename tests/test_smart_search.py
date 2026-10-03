"""Offline checks for direct OCPDB charger search and legacy secret purge."""
import ast
import asyncio
import math
from datetime import datetime, timezone
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "custom_components/driveloom/smart_search.py").read_text()
tree = ast.parse(source)
names = {"_distance_km", "_bearing", "_local_charging", "async_remove_legacy_ai_keys"}
selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in names]
ns = {"Any": object, "HomeAssistant": object, "math": math, "datetime": datetime,
      "timezone": timezone, "BASE": "https://api.mobidata-bw.de/ocpdb/api/public/ocpi/3.0"}
exec(compile(ast.Module(body=selected, type_ignores=[]), "<production>", "exec"), ns)

state = {"api_key": "old-gemini", "tavily_key": "old-tavily", "tavily_usage": {"used": 3},
         "profiles": {"starter": {"kind": "charging"}}}
class Store:
    async def async_load(self): return dict(state)
    async def async_save(self, value): state.clear(); state.update(value)
ns["_read"] = lambda _: Store().async_load()
ns["_store"] = lambda _: Store()
ns["_lock"] = lambda _: asyncio.Lock()
asyncio.run(ns["async_remove_legacy_ai_keys"](object()))
assert state == {"profiles": {"starter": {"kind": "charging"}}}

requests = []
async def fetch(_, msg):
    requests.append(msg)
    return {"warnings": [], "elements": [
        {"id": "352865", "lat": 53.9, "lon": 9.8,
         "tags": {"name": "A7 Süd", "operator": "PRÄG", "addr:city": "Hamburg",
                  "driveloom:power_kw": 320, "driveloom:price_eur_kwh": 0.57,
                  "driveloom:free_count": 2, "driveloom:status_updated": "2026-10-02T20:00:00Z"}},
        {"id": "behind", "lat": 53.7, "lon": 9.8,
         "tags": {"name": "Hinter dem Fahrzeug"}},
    ]}
ns["async_get_pois"] = fetch
profile = {"radius_km": 100, "min_power_kw": 100, "max_price_eur": 0.60,
           "price_mode": "max", "only_available": True}
result = asyncio.run(ns["_local_charging"](object(), profile, 53.8, 9.8, 0))
assert len(result["places"]) == 1
assert result["places"][0]["price_eur_kwh"] == 0.57
assert result["places"][0]["free_count"] == 2
assert requests[0]["connector_filter"] == "ccs" and requests[0]["max_price_eur"] == 0.60
assert result["model"] == "ocpdb" and not result["sources"]
assert "tavily.com" not in source.lower() and "generativelanguage.googleapis.com" not in source.lower()
print("PASS direct OCPDB charging search, direction and legacy key purge")
