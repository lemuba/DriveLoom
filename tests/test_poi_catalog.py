"""Exercise the real catalogue importer and spatial query without an HA server."""
from __future__ import annotations

import ast
import json
import math
import re
import sqlite3
import sys
import tempfile
import types
import unicodedata
from pathlib import Path

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
             "Any": object, "Path": Path, "unicodedata": unicodedata}
catalog = ast.parse((ROOT / "poi_catalog.py").read_text())
selected = [
    node for node in catalog.body
    if isinstance(node, ast.Assign) and any(
        getattr(target, "id", "") in {"_PRIORITY", "_CATEGORY_ORDER", "_TAG_FILTERS"}
        for target in node.targets
    )
    or isinstance(node, ast.FunctionDef) and node.name in {
        "_category", "_normal", "_build_catalog", "_query"
    }
]
exec(compile(ast.Module(body=selected, type_ignores=[]), "<catalog-production>", "exec"), namespace)


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
