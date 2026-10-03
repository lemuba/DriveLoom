"""Station, connector, status, and price join regression checks (offline)."""
import ast
import math
from datetime import datetime
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "custom_components/driveloom/ocpdb.py").read_text()
tree = ast.parse(source)
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in {"_timestamp", "_price", "_connector_key", "_elements"}]
ns = {"Any": object, "math": math, "datetime": datetime, "STATUS_FEED_MAX_AGE": 7200,
      "STATUS_CHANGE_MAX_AGE": 3 * 86400}
exec(compile(ast.Module(body=selected, type_ignores=[]), "<production>", "exec"), ns)

now = ns["_timestamp"]("2026-10-02T20:30:00Z")
location = {"id": "352865", "name": "Öschlesee", "source": "datex2_chargecloud",
            "operator": {"name": "PRÄG"}, "coordinates": {"latitude": 47.68, "longitude": 10.33},
            "charging_pool": [{"evses": [
                {"uid": "evse-1", "status": "AVAILABLE", "status_last_updated": "2026-10-02T20:00:00Z",
                 "connectors": [{"standard": "IEC_62196_T2_COMBO", "max_electric_power": 320000,
                                 "tariff_ids": ["original-tariff"]}]},
                {"uid": "evse-2", "status": "CHARGING", "status_last_updated": "2026-10-02T20:00:00Z",
                 "connectors": [{"standard": "IEC_62196_T2", "max_electric_power": 22000,
                                 "tariff_ids": ["other-tariff"]}]},
            ]}]}
tariffs = {"original-tariff": {"id": "123", "currency": "EUR", "last_updated": "2026-10-02T19:00:00Z",
                               "elements": [{"price_components": [{"type": "ENERGY", "price": 0.57}]}]},
           "other-tariff": {"id": "124", "currency": "EUR",
                            "elements": [{"price_components": [{"type": "ENERGY", "price": 0.21}]}]}}
associations = {"evse-1": {"123"}, "evse-2": {"124"}}
sources = {"datex2_chargecloud": {"realtime_status": "ACTIVE", "realtime_data_updated_at": "2026-10-02T20:10:00Z"}}
def run(**changes):
    msg = {"connector_filter": "ccs", "min_power_kw": 100, "price_mode": "max",
           "max_price_eur": 0.60, "only_available": True}
    msg.update(changes)
    return ns["_elements"]([location], tariffs, associations, sources, msg, now)
assert len(run()) == 1
tags = run()[0]["tags"]
assert tags["driveloom:price_eur_kwh"] == 0.57 and tags["driveloom:power_kw"] == 320
assert tags["driveloom:free_count"] == 1 and tags["driveloom:availability"] == "available"
assert not run(max_price_eur=0.50)
assert not run(min_power_kw=350)
assert not run(min_free=2)
assert ns["_price"]({"currency": "EUR", "elements": [{"price_components": [
    {"type": "ENERGY", "price": 0.5, "taxes": [{"name": "VAT", "percentage": "19"}]}]}]})[0] == 0.595
sources["datex2_chargecloud"]["realtime_data_updated_at"] = "2026-10-01T10:00:00Z"
assert not run()
sources["datex2_chargecloud"]["realtime_data_updated_at"] = "2026-10-02T20:10:00Z"
associations["evse-1"] = set()
assert not run()
print("PASS OCPDB connector-specific status and ad-hoc tariff joins")
