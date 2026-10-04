"""Exercise production automatic GPS trigger logic without a Home Assistant runtime."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

source = (Path(__file__).resolve().parents[1] / "custom_components/driveloom/gps_sources.py").read_text()
tree = ast.parse(source)
mixin = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GPSSourcesMixin")
methods = [n for n in mixin.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
           and n.name in {"_source_action", "_auto_trigger_entity", "_auto_connected", "_listen_auto", "_reconcile_auto"}]
namespace = {"LOCATION_INTERVALS": {0, 10, 20, 30, 60, 120, 300, 600},
             "POINT_FILTERS": {"off", "detailed", "balanced", "compact"},
             "callback": lambda fn: fn}
listeners = []
namespace["async_track_state_change_event"] = lambda hass, entities, changed: (
    listeners.append(entities), lambda: None)[1]
exec(compile(ast.Module(body=methods, type_ignores=[]), "gps_sources.py", "exec"), namespace)
Harness = type("Harness", (), {n.name: namespace[n.name] for n in methods})
manager = Harness()
states = {"sensor.phone_ssid": SimpleNamespace(state="CarPlay"),
          "binary_sensor.car_connected": SimpleNamespace(state="off")}
manager.hass = SimpleNamespace(states=SimpleNamespace(get=states.get),
                               services=SimpleNamespace(has_service=lambda *args: True))
manager._entries = {"a": object(), "b": object()}
manager._sources = {"phone": {"vehicles": ["a", "b"]}}
manager._auto_rules = {}
manager._sessions = {}
manager._auto_unsubs = {}
manager._cancel_auto_timer = lambda entry_id: None
manager._cancel_location_poll = lambda entry_id: None

def rejects(payload):
    try:
        manager._source_action("auto_save", payload)
    except ValueError:
        return
    raise AssertionError(f"accepted invalid automatic trigger: {payload}")

legacy = {"source_id": "phone", "ssid_entity": "sensor.phone_ssid", "ssid": "CarPlay"}
assert manager._auto_trigger_entity(legacy) == "sensor.phone_ssid"
assert manager._auto_connected(legacy)
manager._auto_rules["a"] = legacy
manager._listen_auto("a")
assert listeners[-1] == ["sensor.phone_ssid"]

binary = {"entry_id": "a", "source_id": "phone", "trigger_type": "binary_sensor",
          "binary_entity": "binary_sensor.car_connected"}
manager._source_action("auto_save", binary)
rule = manager._auto_rules["a"]
assert rule["trigger_type"] == "binary_sensor" and rule["ssid"] == ""
assert not manager._auto_connected(rule)
manager._listen_auto("a")
assert listeners[-1] == ["binary_sensor.car_connected"]
states["binary_sensor.car_connected"].state = "on"
assert manager._auto_connected(rule)
states["binary_sensor.car_connected"].state = "unknown"
assert not manager._auto_connected(rule)
rejects({**binary, "binary_entity": "sensor.phone_ssid"})
rejects({**binary, "binary_entity": "binary_sensor.absent"})
rejects({**binary, "entry_id": "b"})
rejects({**binary, "trigger_type": "other"})

manager._source_action("auto_save", {"entry_id": "b", "source_id": "phone", "ssid_entity": "sensor.phone_ssid", "ssid": "CarPlay"})
assert manager._auto_rules["b"]["trigger_type"] == "ssid"
assert manager._auto_connected(manager._auto_rules["b"])

async def check_transitions():
    states["binary_sensor.car_connected"].state = "off"
    manager._auto_rules["a"] = rule
    manager._source_lock = asyncio.Lock()
    manager._auto_timers = {}
    manager._final_fix_tasks = {}
    manager._cancel_final_fix = lambda entry_id: None
    manager._cancel_auto_timer = lambda entry_id: None
    manager._cancel_location_poll = lambda entry_id: None
    manager._sync_location_poll = lambda entry_id: None
    manager._schedule_sample = lambda entry_id, delay: None
    saved = []
    async def persist():
        saved.append(True)
    async def action(action, payload):
        assert action == "start" and payload["mode"] == "auto"
        manager._sessions[payload["entry_id"]] = {"active": True, "mode": "auto", "suspended": False, "token": "test"}
    manager._persist_sources = persist
    manager.async_source_action = action
    manager.hass.async_create_task = lambda coro: (coro.close(), object())[1]
    manager._auto_disconnect = lambda entry_id, token: asyncio.sleep(90)
    states["binary_sensor.car_connected"].state = "on"
    await manager._reconcile_auto("a")
    session = manager._sessions["a"]
    assert session["active"] and not session["suspended"]
    states["binary_sensor.car_connected"].state = "off"
    await manager._reconcile_auto("a")
    assert session["suspended"] and "a" in manager._auto_timers and saved
    states["binary_sensor.car_connected"].state = "on"
    await manager._reconcile_auto("a")
    assert not session["suspended"] and not session.get("final_until")
    session["active"] = False
    rule["blocked"] = True
    await manager._reconcile_auto("a")
    assert not session["active"]
    states["binary_sensor.car_connected"].state = "off"
    await manager._reconcile_auto("a")
    assert not rule["blocked"]

asyncio.run(check_transitions())
print("PASS legacy SSID, binary validation, listener, start/pause/resume and blocked restart")
