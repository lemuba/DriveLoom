"""Exercise the real catalogue importer and spatial query without an HA server."""
from __future__ import annotations

import ast
import asyncio
import importlib.util
import json
import math
import re
import sqlite3
import struct
import sys
import tempfile
import types
import unicodedata
import zlib
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "driveloom"
source = ast.parse((ROOT / "poi.py").read_text())
clauses = ast.literal_eval(next(
    node.value for node in source.body
    if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "POI_CLAUSES"
))


def distance(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    delta = math.radians(d - b)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(delta / 2) ** 2
    return 6371008.8 * 2 * math.asin(math.sqrt(x))


namespace = {"POI_CLAUSES": clauses, "re": re, "sqlite3": sqlite3, "json": json,
             "math": math, "time": __import__("time"), "_haversine_m": distance,
             "Any": object, "Path": Path, "unicodedata": unicodedata,
             "urlsplit": urlsplit, "INDEX_MAX_BYTES": 8 * 1024 * 1024}
spec = importlib.util.spec_from_file_location("driveloom_pbf_test", ROOT / "pbf_reader.py")
pbf_reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pbf_reader)
namespace["pbf_entities"] = pbf_reader.entities
catalog = ast.parse((ROOT / "poi_catalog.py").read_text())
selected = [
    node for node in catalog.body
    if isinstance(node, ast.Assign) and any(
        getattr(target, "id", "") in {"_PRIORITY", "_CATEGORY_ORDER", "_TAG_FILTERS"}
        for target in node.targets
    )
    or isinstance(node, ast.FunctionDef) and node.name in {
        "_category", "_normal", "_build_catalog", "_query", "_valid_pbf_url",
        "_parse_index", "_merge_country_results", "_intersects"
    }
    or isinstance(node, ast.AsyncFunctionDef) and node.name == "_read_index"
]
exec(compile(ast.Module(body=selected, type_ignores=[]), "<catalog-production>", "exec"), namespace)
namespace["_LEGACY_PATHS"] = {"europe/germany": "germany"}

index = {"type": "FeatureCollection", "features": [
    {"properties": {"id": f"europe/country-{i}", "name": f"Country {i}",
                    "iso3166-1:alpha2": ["DE"],
                    "urls": {"pbf": f"https://download.geofabrik.de/europe/country-{i}-latest.osm.pbf"}}}
    for i in range(21)
] + [{"properties": {"id": "europe/evil", "name": "Evil",
                     "iso3166-1:alpha2": ["XX"],
                     "urls": {"pbf": "https://example.org/evil-latest.osm.pbf"}}}]}
assert len(namespace["_parse_index"](index)) == 21
assert not namespace["_intersects"]([50, 8, 51, 9], 54, 10, 20)
assert namespace["_intersects"]([50, 8, 55, 12], 54, 10, 20)
shared = {"type": "node", "id": 23, "lat": 54, "lon": 10}
other = {"type": "way", "id": 24, "lat": 54.1, "lon": 10}
assert namespace["_merge_country_results"]([[shared], [shared, other]], 54, 10, 10) == [shared, other]


class ChunkedContent:
    def __init__(self, chunks):
        self.chunks = chunks

    async def iter_chunked(self, _size):
        for chunk in self.chunks:
            yield chunk


payload = json.dumps({**index, "description": "x" * 9000}).encode()
assert len(payload) > 8192
body = asyncio.run(namespace["_read_index"](
    types.SimpleNamespace(content=ChunkedContent([payload[:8192], payload[8192:]]))
))
assert body == payload and len(namespace["_parse_index"](json.loads(body))) == 21
try:
    asyncio.run(namespace["_read_index"](
        types.SimpleNamespace(content=ChunkedContent([b"x" * (4 * 1024 * 1024),
                                                      b"x" * (4 * 1024 * 1024 + 1)]))
    ))
except ValueError as err:
    assert "zu groß" in str(err)
else:
    raise AssertionError("Oversized index must be rejected")
print("PASS country index reads all chunks and enforces its size limit")


class Location:
    def __init__(self, lat, lon):
        self.lat, self.lon = lat, lon

    def valid(self):
        return True


class Node:
    def __init__(self, number, tags, lat, lon):
        self.id, self.tags, self.location = number, tags, Location(lat, lon)


class OsmiumHandler:
    pass


class Locations:
    def __init__(self, index):
        assert index == "flex_mem"

    def ignore_errors(self):
        self.ignores_missing = True


def apply(filename, locations, handler):
    assert locations.ignores_missing
    for item in nodes:
        handler.node(item)


sys.modules["osmium"] = types.SimpleNamespace(
    SimpleHandler=OsmiumHandler, NodeLocationsForWays=Locations,
    index=types.SimpleNamespace(create_map=lambda key: key), apply=apply
)
nodes = [
    Node(i + 1, {"amenity": "fast_food", "brand": "McDonald's", "name": f"Filiale {i}"},
         53.5 + (i % 75) * .002, 9.5 + (i // 75) * .002)
    for i in range(4000)
]
nodes.append(Node(5000, {"amenity": "fuel", "name": "Tankstelle"}, 53.55, 9.55))
nodes.append(Node(5001, {"amenity": "parking", "parking": "underground"}, 53.55, 9.55))
nodes.append(Node(5002, {"amenity": "charging_station"}, 53.55, 9.55))
nodes.append(Node(5003, {"amenity": "fast_food"}, 58.0, 9.55))

with tempfile.TemporaryDirectory() as temp:
    target = Path(temp) / "catalog.db"
    count = namespace["_build_catalog"](Path(temp) / "fake.pbf", target, "germany")
    assert count == 4003, count
    with sqlite3.connect(target) as con:
        assert con.execute("SELECT COUNT(*) FROM positions").fetchone()[0] == count
        assert con.execute("SELECT category FROM pois WHERE osm_id=5001").fetchone()[0] == "parking_garage"
    results, examined = namespace["_query"](
        target, "germany", 53.5, 9.5, 100, ["restaurant"], "mcdonalds", 3000
    )
    assert len(results) == 3000 and examined >= 3000
    assert len({item["id"] for item in results}) == 3000
    assert all(item["tags"]["brand"] == "McDonald's" for item in results)
    assert namespace["_query"](
        target, "germany", 53.5, 9.5, 100, ["restaurant"], "", 2000,
        (53.5, 9.5, 53.51, 9.51),
    )[0]
    assert namespace["_query"](
        target, "schleswig-holstein", 53.5, 9.5, 100, ["restaurant"], "", 2000
    )[0] == []
    assert namespace["_query"](
        target, "germany", 53.5, 9.5, 100, ["charging"], "", 2000
    )[0] == []
print("PASS regional catalogue indexes, brand search, 3000 results, bounds and region isolation")


def varint(number):
    result = bytearray()
    while number > 127:
        result.append((number & 127) | 128)
        number >>= 7
    result.append(number)
    return bytes(result)


def sint(number):
    return (number << 1) ^ (number >> 63)


def field(number, value):
    if isinstance(value, int):
        return varint(number << 3) + varint(value)
    return varint((number << 3) | 2) + varint(len(value)) + value


def packed(*values):
    return b"".join(varint(value) for value in values)


strings = [b"", b"amenity", b"fast_food", b"name", b"Testbistro", b"parking", b"Wayplatz"]
string_table = b"".join(field(1, item) for item in strings)
# Dense nodes 101 and 102. The POI way references them, including its closing node.
dense = b"".join((field(1, packed(sint(101), sint(1))),
                  field(8, packed(sint(535000000), sint(10000))),
                  field(9, packed(sint(95000000), sint(10000))),
                  field(10, packed(1, 2, 3, 4, 0, 0))))
way = b"".join((field(1, 901), field(2, packed(1, 3)),
                field(3, packed(5, 6)),
                field(8, packed(sint(101), sint(1), sint(-1)))))
primitive = field(1, string_table) + field(2, field(2, dense) + field(3, way))
blob = field(2, len(primitive)) + field(3, zlib.compress(primitive))
header = field(1, b"OSMData") + field(3, len(blob))

with tempfile.TemporaryDirectory() as temp:
    source = Path(temp) / "fixture.osm.pbf"
    source.write_bytes(struct.pack(">I", len(header)) + header + blob)
    # Force the fallback, so no platform package is needed for this test.
    sys.modules["osmium"] = None
    target = Path(temp) / "fallback.db"
    assert namespace["_build_catalog"](source, target, "europe/testland") == 2
    with sqlite3.connect(target) as con:
        rows = con.execute("SELECT osm_type,osm_id,lat,lon FROM pois ORDER BY osm_id").fetchall()
        assert len(rows) == 2 and rows[0][0] == "node" and rows[1][0] == "way", rows
        assert abs(rows[1][2] - (53.5 * 2 + 53.501) / 3) < .000001, rows
    assert len(namespace["_query"](target, "europe/testland", 53.5, 9.5, 5,
                                   ["restaurant", "parking"], "", 10)[0]) == 2
print("PASS dependency-free PBF importer: dense nodes, way coordinates, catalogue query")
