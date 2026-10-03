"""Exercise pagination, Germany selection and persistent cache without HA/network."""
import ast
import asyncio
import importlib.util
import math
import sqlite3
import tempfile
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
source = (root / "custom_components/driveloom/ocpdb.py").read_text()
cache_spec = importlib.util.spec_from_file_location(
    "ocpdb_cache", root / "custom_components/driveloom/ocpdb_cache.py")
cache = importlib.util.module_from_spec(cache_spec)
cache_spec.loader.exec_module(cache)
tree = ast.parse(source)
selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"_timestamp", "_price", "_connector_key", "_elements", "async_get_pois"}]


class Response:
    status = 200
    content_length = 1

    def __init__(self, data):
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def read(self):
        return b"{}"

    async def json(self, content_type=None):
        return self.data


class Session:
    def __init__(self):
        self.calls = []
        self.fail_offset = None

    def get(self, url, params=None, **kwargs):
        self.calls.append((url, params))
        if url.endswith("/locations"):
            assert params["offset"] <= 5501, "Pagination did not stop at total_count"
        if url.endswith("/sources"):
            return Response({"items": [{"uid": "de_feed", "realtime_status": "ACTIVE",
                                         "realtime_data_updated_at": datetime.now().astimezone().isoformat()}]})
        if url.endswith("/tariffs") or url.endswith("/tariff-associations"):
            return Response({"items": [], "total_count": 0})
        assert url.endswith("/locations") and params["country"] == "DEU"
        offset = params["offset"]
        if offset == self.fail_offset:
            raise OSError("interrupted page")
        count = min(1000, 5501 - offset)
        return Response({"items": [{"id": str(n), "name": f"Station {n}", "source": "de_feed",
                                    "coordinates": {"latitude": 54 + n / 100000, "longitude": 9.8},
                                    "charging_pool": [{"evses": [{"uid": str(n), "connectors": [{
                                        "standard": "IEC_62196_T2_COMBO", "max_electric_power": 150000}]}]}]}
                                   for n in range(offset, offset + count)], "total_count": 5501})


async def main():
    async def executor(fn, *args):
        return fn(*args)
    with tempfile.TemporaryDirectory() as directory:
        session = Session()
        config = SimpleNamespace(path=lambda *parts: str(Path(directory).joinpath(*parts)))
        hass = SimpleNamespace(data={}, config=config, async_add_executor_job=executor)
        namespace = {"Any": object, "asyncio": asyncio, "aiohttp": SimpleNamespace(
            ClientTimeout=lambda **_: None, ClientError=OSError), "time": time, "math": math,
            "sqlite3": sqlite3, "Path": Path, "datetime": datetime,
            "async_get_clientsession": lambda _: session, "ocpdb_cache": cache,
            "BASE": "https://example.test/ocpi", "SOURCES": "https://example.test/sources",
            "PAGE_SIZE": 1000, "MAX_LOCATIONS": 100000, "DOMAIN": "driveloom",
            "_STATE": "ocpdb_state", "STATUS_FEED_MAX_AGE": 7200,
            "STATUS_CHANGE_MAX_AGE": 3 * 86400,
            "_LOGGER": SimpleNamespace(warning=lambda *args: None)}
        exec(compile(ast.Module(body=selected, type_ignores=[]), "<production>", "exec"), namespace)
        query = {"latitude": 54, "longitude": 9.8, "radius_km": 1000,
                 "min_power_kw": 100, "max_results": 6000}
        first = await namespace["async_get_pois"](hass, query)
        assert len(first["elements"]) == 5501
        assert not first["candidate_limit_hit"]
        assert [p["offset"] for url, p in session.calls if url.endswith("/locations")] == list(range(0, 6000, 1000))
        assert (Path(directory) / ".storage" / "driveloom-ocpdb.db").exists()
        session.calls.clear()
        hass.data = {}
        second = await namespace["async_get_pois"](hass, query)
        assert len(second["elements"]) == 5501 and not session.calls
        session.fail_offset = 1000
        failed = await namespace["async_get_pois"](hass, {**query, "force_refresh": True})
        assert len(failed["elements"]) == 5501
        assert "gespeicherte Standorte" in failed["warnings"][0]
        assert len(cache.read(Path(directory) / ".storage" / cache.DB_FILENAME,
                              "54.0:9.8:1000:DEU")[1]["locations"]) == 5501
        print("PASS German pagination beyond 5,000, SQLite reuse and atomic failed-page fallback")


asyncio.run(main())
