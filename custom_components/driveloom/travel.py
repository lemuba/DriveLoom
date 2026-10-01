"""Travel planning and archive storage for DriveLoom.

Folder, POI and note records live in DriveLoom's main database. Binary documents
live in one dedicated SQLite database. All endpoints require an authenticated
Home Assistant WebSocket connection; no document is exposed as a static path.
"""

from __future__ import annotations

import base64
import asyncio
import hashlib
import json
import math
import os
import sqlite3
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .db import connect, db_path

DOC_DB = "driveloom-documents.db"
DEFAULT_QUOTA = 100 * 1024 * 1024
MAX_CHUNK = 256 * 1024
STORE_KEY = "travel_transfers"
SEARCH_KEY = "travel_search"
PHOTON_URL = "https://photon.komoot.io/api/"


def _doc_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(".storage", DOC_DB))


def _initialize(main: Path, docs: Path) -> None:
    with connect(main) as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS travel_folders (
                id TEXT PRIMARY KEY, parent_id TEXT REFERENCES travel_folders(id),
                name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('folder','trip')),
                status TEXT NOT NULL DEFAULT 'planned', position INTEGER NOT NULL DEFAULT 0,
                quota_bytes INTEGER NOT NULL DEFAULT 104857600,
                created REAL NOT NULL, updated REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS travel_folder_parent ON travel_folders(parent_id);
            CREATE TABLE IF NOT EXISTS travel_pois (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
                source TEXT NOT NULL, source_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS travel_assignments (
                folder_id TEXT NOT NULL REFERENCES travel_folders(id) ON DELETE CASCADE,
                poi_id TEXT NOT NULL REFERENCES travel_pois(id) ON DELETE CASCADE,
                day TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(folder_id,poi_id)
            );
            CREATE TABLE IF NOT EXISTS travel_notes (
                id TEXT PRIMARY KEY,
                folder_id TEXT REFERENCES travel_folders(id) ON DELETE CASCADE,
                poi_id TEXT REFERENCES travel_pois(id) ON DELETE CASCADE,
                body TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
                CHECK(folder_id IS NOT NULL OR poi_id IS NOT NULL)
            );
        """)
    with connect(docs) as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, folder_id TEXT NOT NULL, trip_id TEXT NOT NULL,
                filename TEXT NOT NULL, title TEXT NOT NULL, mime TEXT NOT NULL,
                size INTEGER NOT NULL, sha256 TEXT NOT NULL, created REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS document_chunks (
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                part_index INTEGER NOT NULL, content BLOB NOT NULL,
                PRIMARY KEY(document_id,part_index)
            );
            CREATE INDEX IF NOT EXISTS documents_trip ON documents(trip_id);
            CREATE INDEX IF NOT EXISTS documents_folder ON documents(folder_id);
        """)


def _tree(con: sqlite3.Connection, folder_id: str) -> list[str]:
    return [row[0] for row in con.execute("""
        WITH RECURSIVE branch(id) AS (
            SELECT id FROM travel_folders WHERE id=?
            UNION ALL SELECT f.id FROM travel_folders f JOIN branch b ON f.parent_id=b.id
        ) SELECT id FROM branch
    """, (folder_id,))]


def _trip(con: sqlite3.Connection, folder_id: str) -> str:
    current = folder_id
    seen: set[str] = set()
    while current and current not in seen:
        seen.add(current)
        row = con.execute("SELECT parent_id,kind FROM travel_folders WHERE id=?", (current,)).fetchone()
        if row is None:
            raise ValueError("Ordner nicht gefunden")
        if row["kind"] == "trip":
            return current
        current = row["parent_id"]
    raise ValueError("Dokumente brauchen einen als Reise markierten Ordner")


def _snapshot(main: Path, docs: Path) -> dict[str, Any]:
    _initialize(main, docs)
    with connect(main) as con:
        folders = [dict(row) for row in con.execute("SELECT * FROM travel_folders ORDER BY position,created")]
        pois = [dict(row) for row in con.execute("SELECT * FROM travel_pois ORDER BY name")]
        for poi in pois:
            poi["metadata"] = json.loads(poi.pop("metadata_json"))
        assignments = [dict(row) for row in con.execute("SELECT * FROM travel_assignments ORDER BY position")]
        notes = [dict(row) for row in con.execute("SELECT * FROM travel_notes ORDER BY created")]
    with connect(docs) as con:
        documents = [dict(row) for row in con.execute(
            "SELECT id,folder_id,trip_id,filename,title,mime,size,sha256,created "
            "FROM documents ORDER BY created DESC")]
    return {"folders": folders, "pois": pois, "assignments": assignments,
            "notes": notes, "documents": documents}


def _change(main: Path, docs: Path, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    _initialize(main, docs)
    now = time.time()
    with connect(main) as con:
        if action == "folder_save":
            identifier = str(payload.get("id") or uuid.uuid4().hex)
            parent = payload.get("parent_id") or None
            if parent is not None and not con.execute("SELECT 1 FROM travel_folders WHERE id=?", (parent,)).fetchone():
                raise ValueError("Zielordner nicht gefunden")
            if parent == identifier or parent in _tree(con, identifier):
                raise ValueError("Ein Ordner kann nicht in seinen eigenen Unterbaum verschoben werden")
            name = str(payload.get("name", "")).strip()[:120]
            if not name:
                raise ValueError("Ordnername fehlt")
            kind = payload.get("kind", "folder")
            status = payload.get("status", "planned")
            if kind not in ("folder", "trip") or status not in ("planned", "traveling", "archived"):
                raise ValueError("Ungültige Ordnerangaben")
            quota_mb = int(payload.get("quota_mb", 100))
            if not 1 <= quota_mb <= 100000:
                raise ValueError("Reisegröße außerhalb des erlaubten Bereichs")
            old = con.execute("SELECT * FROM travel_folders WHERE id=?", (identifier,)).fetchone()
            if old and old["kind"] == "trip":
                with connect(docs) as dc:
                    used = dc.execute("SELECT COALESCE(SUM(size),0) FROM documents WHERE trip_id=?",
                                      (identifier,)).fetchone()[0]
                if used > quota_mb * 1024 * 1024:
                    raise ValueError("Das neue Gesamtvolumen liegt unter den gespeicherten Dokumenten")
            if old and old["kind"] == "trip" and kind != "trip":
                with connect(docs) as dc:
                    if dc.execute("SELECT 1 FROM documents WHERE trip_id=? LIMIT 1", (identifier,)).fetchone():
                        raise ValueError("Reise mit Dokumenten kann nicht in einen normalen Ordner umgewandelt werden")
            con.execute("""INSERT INTO travel_folders VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET parent_id=excluded.parent_id,name=excluded.name,
                kind=excluded.kind,status=excluded.status,position=excluded.position,
                quota_bytes=excluded.quota_bytes,updated=excluded.updated""",
                (identifier, parent, name, kind, status, int(payload.get("position", 0)),
                 quota_mb * 1024 * 1024, old["created"] if old else now, now))
            if old and (old["parent_id"] != parent or old["kind"] != kind):
                branch = set(_tree(con, identifier))
                with connect(docs) as dc:
                    records = [dict(row) for row in dc.execute("SELECT id,folder_id,trip_id,size FROM documents")]
                    changed = [(row["id"], _trip(con, row["folder_id"]))
                               for row in records if row["folder_id"] in branch]
                    planned = dict(changed)
                    totals: dict[str, int] = {}
                    for row in records:
                        destination = planned.get(row["id"], row["trip_id"])
                        totals[destination] = totals.get(destination, 0) + row["size"]
                    for trip_id, total in totals.items():
                        limit = con.execute("SELECT quota_bytes FROM travel_folders WHERE id=?", (trip_id,)).fetchone()
                        if limit is None or total > limit[0]:
                            raise ValueError("Verschieben würde das Gesamtvolumen einer Reise überschreiten")
                    dc.executemany("UPDATE documents SET trip_id=? WHERE id=?",
                                   [(trip_id, doc_id) for doc_id, trip_id in changed])
            result = {"id": identifier}
        elif action == "folder_delete":
            identifier = str(payload.get("id", ""))
            ids = _tree(con, identifier)
            if not ids:
                raise ValueError("Ordner nicht gefunden")
            with connect(docs) as dc:
                dc.executemany("DELETE FROM documents WHERE folder_id=?", [(key,) for key in ids])
            for key in reversed(ids):
                con.execute("DELETE FROM travel_folders WHERE id=?", (key,))
            result = {"deleted": len(ids)}
        elif action == "poi_save":
            identifier = str(payload.get("id") or uuid.uuid4().hex)
            name = str(payload.get("name", "")).strip()[:160]
            lat, lon = float(payload.get("lat", float("nan"))), float(payload.get("lon", float("nan")))
            if not name or not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("POI braucht Namen und gültige Koordinaten")
            metadata = payload.get("metadata", {})
            if not isinstance(metadata, dict) or len(json.dumps(metadata)) > 16000:
                raise ValueError("POI-Metadaten sind ungültig oder zu groß")
            retained = {str(k)[:80]: str(v)[:2000] for k, v in metadata.items() if v is not None}
            old = con.execute("SELECT created FROM travel_pois WHERE id=?", (identifier,)).fetchone()
            con.execute("""INSERT INTO travel_pois VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,lat=excluded.lat,lon=excluded.lon,
                source=excluded.source,source_id=excluded.source_id,
                metadata_json=excluded.metadata_json,updated=excluded.updated""",
                (identifier, name, lat, lon, str(payload.get("source", "manual"))[:40],
                 str(payload.get("source_id", ""))[:200], json.dumps(retained, ensure_ascii=False),
                 old["created"] if old else now, now))
            result = {"id": identifier}
        elif action == "poi_delete":
            con.execute("DELETE FROM travel_pois WHERE id=?", (payload.get("id"),))
            result = {"deleted": con.total_changes > 0}
        elif action == "assign":
            folder_id, poi_id = str(payload.get("folder_id", "")), str(payload.get("poi_id", ""))
            con.execute("INSERT INTO travel_assignments VALUES (?,?,?,?) ON CONFLICT(folder_id,poi_id) "
                        "DO UPDATE SET day=excluded.day,position=excluded.position",
                        (folder_id, poi_id, str(payload.get("day", ""))[:40], int(payload.get("position", 0))))
            result = {"folder_id": folder_id, "poi_id": poi_id}
        elif action == "unassign":
            con.execute("DELETE FROM travel_assignments WHERE folder_id=? AND poi_id=?",
                        (payload.get("folder_id"), payload.get("poi_id")))
            result = {"deleted": True}
        elif action == "note_save":
            identifier = str(payload.get("id") or uuid.uuid4().hex)
            folder_id, poi_id = payload.get("folder_id") or None, payload.get("poi_id") or None
            body = str(payload.get("body", ""))
            if not (folder_id or poi_id) or len(body) > 100000:
                raise ValueError("Notiz braucht ein Ziel und darf höchstens 100.000 Zeichen enthalten")
            old = con.execute("SELECT created FROM travel_notes WHERE id=?", (identifier,)).fetchone()
            con.execute("INSERT INTO travel_notes VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE "
                        "SET folder_id=excluded.folder_id,poi_id=excluded.poi_id,body=excluded.body,updated=excluded.updated",
                        (identifier, folder_id, poi_id, body, old["created"] if old else now, now))
            result = {"id": identifier}
        elif action == "note_delete":
            con.execute("DELETE FROM travel_notes WHERE id=?", (payload.get("id"),))
            result = {"deleted": True}
        elif action == "document_delete":
            with connect(docs) as dc:
                dc.execute("DELETE FROM documents WHERE id=?", (payload.get("id"),))
            result = {"deleted": True}
        elif action == "document_rename":
            title = str(payload.get("title", "")).strip()[:200]
            if not title:
                raise ValueError("Dokumenttitel fehlt")
            with connect(docs) as dc:
                dc.execute("UPDATE documents SET title=? WHERE id=?", (title, payload.get("id")))
            result = {"id": payload.get("id")}
        elif action == "quota":
            folder_id = str(payload.get("folder_id", ""))
            limit = int(payload.get("quota_mb", 0))
            if not 1 <= limit <= 100000:
                raise ValueError("Ungültige Reisegröße")
            with connect(docs) as dc:
                used = dc.execute("SELECT COALESCE(SUM(size),0) FROM documents WHERE trip_id=?", (folder_id,)).fetchone()[0]
            if used > limit * 1024 * 1024:
                raise ValueError("Das neue Gesamtvolumen liegt unter den gespeicherten Dokumenten")
            con.execute("UPDATE travel_folders SET quota_bytes=?,updated=? WHERE id=? AND kind='trip'",
                        (limit * 1024 * 1024, now, folder_id))
            result = {"folder_id": folder_id}
        else:
            raise ValueError("Unbekannte Reiseaktion")
    return result


def _save_document(main: Path, docs: Path, transfer: dict[str, Any]) -> dict[str, Any]:
    _initialize(main, docs)
    with connect(main) as con:
        trip_id = _trip(con, transfer["folder_id"])
        quota = con.execute("SELECT quota_bytes FROM travel_folders WHERE id=?", (trip_id,)).fetchone()[0]
    with connect(docs) as con:
        used = con.execute("SELECT COALESCE(SUM(size),0) FROM documents WHERE trip_id=?", (trip_id,)).fetchone()[0]
        if used + transfer["size"] > quota:
            raise ValueError("Dieses Dokument überschreitet das Gesamtvolumen der Reise")
        identifier = uuid.uuid4().hex
        con.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?)",
                    (identifier, transfer["folder_id"], trip_id, transfer["filename"],
                     transfer["title"], transfer["mime"], transfer["size"],
                     transfer["sha256"], time.time()))
        with Path(transfer["path"]).open("rb") as source:
            for index, chunk in enumerate(iter(lambda: source.read(MAX_CHUNK), b"")):
                con.execute("INSERT INTO document_chunks VALUES (?,?,?)",
                            (identifier, index, sqlite3.Binary(chunk)))
    return {"id": identifier}


def _document_chunk(docs: Path, identifier: str, offset: int) -> dict[str, Any]:
    with connect(docs) as con:
        if offset % MAX_CHUNK:
            raise ValueError("Ungültiger Dokument-Offset")
        row = con.execute("SELECT filename,mime,size FROM documents WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError("Dokument nicht gefunden")
        part = con.execute("SELECT content FROM document_chunks WHERE document_id=? AND part_index=?",
                           (identifier, offset // MAX_CHUNK)).fetchone()
        if offset < row["size"] and part is None:
            raise ValueError("Dokumentblock fehlt")
        return {"filename": row["filename"], "mime": row["mime"], "size": row["size"],
                "offset": offset, "content": base64.b64encode(part[0] if part else b"").decode("ascii")}


def _export(main: Path, docs: Path, destination: Path, folder_id: str) -> int:
    data = _snapshot(main, docs)
    if folder_id:
        with connect(main) as con:
            branch = set(_tree(con, folder_id))
            ids = set(branch)
            parent = con.execute("SELECT parent_id FROM travel_folders WHERE id=?", (folder_id,)).fetchone()
            while parent and parent[0]:
                ids.add(parent[0])
                parent = con.execute("SELECT parent_id FROM travel_folders WHERE id=?", (parent[0],)).fetchone()
        if not ids:
            raise ValueError("Reiseordner nicht gefunden")
        data["folders"] = [f for f in data["folders"] if f["id"] in ids]
        data["assignments"] = [a for a in data["assignments"] if a["folder_id"] in branch]
        poi_ids = {a["poi_id"] for a in data["assignments"]}
        data["pois"] = [p for p in data["pois"] if p["id"] in poi_ids]
        data["notes"] = [n for n in data["notes"] if n["folder_id"] in branch or
                         n["folder_id"] is None and n["poi_id"] in poi_ids]
        data["documents"] = [d for d in data["documents"] if d["folder_id"] in branch]
    manifest = {"format": "driveloom-travel-beta-1", "exported": time.time(), **data}
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        archive.writestr("reise.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        with connect(docs) as con:
            for document in data["documents"]:
                with archive.open(f"dokumente/{document['id']}/{document['filename']}", "w") as output:
                    size = 0
                    for row in con.execute("SELECT content FROM document_chunks WHERE document_id=? ORDER BY part_index",
                                           (document["id"],)):
                        output.write(row[0])
                        size += len(row[0])
                    if size != document["size"]:
                        raise ValueError("Ein Dokument ist während des Exports unvollständig")
    return destination.stat().st_size


def _restore(main: Path, docs: Path, source: Path) -> dict[str, int]:
    """Restore a complete DriveLoom travel archive into an empty travel store."""
    _initialize(main, docs)
    with connect(main) as con, connect(docs) as dc:
        if any(con.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
               for table in ("travel_folders", "travel_pois", "travel_notes", "travel_assignments")) or \
                dc.execute("SELECT 1 FROM documents LIMIT 1").fetchone():
            raise ValueError("Wiederherstellung nur in ein leeres Reisearchiv möglich")
    with zipfile.ZipFile(source) as archive:
        manifest = json.loads(archive.read("reise.json"))
        if manifest.get("format") != "driveloom-travel-beta-1":
            raise ValueError("Unbekanntes Reiseexport-Format")
        for key in ("folders", "pois", "assignments", "notes", "documents"):
            if not isinstance(manifest.get(key), list):
                raise ValueError("Reiseexport ist unvollständig")
        folders = manifest["folders"]
        folder_ids = {f["id"] for f in folders}
        poi_ids = {p["id"] for p in manifest["pois"]}
        if len(folder_ids) != len(folders) or len(poi_ids) != len(manifest["pois"]):
            raise ValueError("Doppelte IDs im Reiseexport")
        if any(f["parent_id"] and f["parent_id"] not in folder_ids for f in folders):
            raise ValueError("Fehlender Elternordner im Reiseexport")
        if any(a["folder_id"] not in folder_ids or a["poi_id"] not in poi_ids
               for a in manifest["assignments"]):
            raise ValueError("Ungültige POI-Zuordnung im Reiseexport")
        if any((n["folder_id"] and n["folder_id"] not in folder_ids) or
               (n["poi_id"] and n["poi_id"] not in poi_ids) for n in manifest["notes"]):
            raise ValueError("Ungültige Notiz im Reiseexport")
        totals: dict[str, int] = {}
        for doc in manifest["documents"]:
            if doc["folder_id"] not in folder_ids or doc["trip_id"] not in folder_ids:
                raise ValueError("Ungültige Dokumentzuordnung im Reiseexport")
            name = f"dokumente/{doc['id']}/{doc['filename']}"
            if name not in archive.namelist() or archive.getinfo(name).file_size != doc["size"]:
                raise ValueError("Dokument fehlt oder hat eine falsche Größe")
            totals[doc["trip_id"]] = totals.get(doc["trip_id"], 0) + doc["size"]
        quotas = {f["id"]: f["quota_bytes"] for f in folders if f["kind"] == "trip"}
        if any(key not in quotas or used > quotas[key] for key, used in totals.items()):
            raise ValueError("Dokumente überschreiten das Reisevolumen")
        try:
            with connect(main) as con:
                pending = list(folders)
                inserted: set[str] = set()
                while pending:
                    ready = [f for f in pending if not f["parent_id"] or f["parent_id"] in inserted]
                    if not ready:
                        raise ValueError("Zyklische Ordnerstruktur im Reiseexport")
                    for f in ready:
                        con.execute("INSERT INTO travel_folders VALUES (?,?,?,?,?,?,?,?,?)",
                                    tuple(f[key] for key in ("id", "parent_id", "name", "kind", "status",
                                                              "position", "quota_bytes", "created", "updated")))
                        inserted.add(f["id"])
                        pending.remove(f)
                con.executemany("INSERT INTO travel_pois VALUES (?,?,?,?,?,?,?,?,?)", [
                    (p["id"], p["name"], p["lat"], p["lon"], p["source"], p["source_id"],
                     json.dumps(p["metadata"], ensure_ascii=False), p["created"], p["updated"])
                    for p in manifest["pois"]])
                con.executemany("INSERT INTO travel_assignments VALUES (?,?,?,?)", [
                    tuple(a[key] for key in ("folder_id", "poi_id", "day", "position"))
                    for a in manifest["assignments"]])
                con.executemany("INSERT INTO travel_notes VALUES (?,?,?,?,?,?)", [
                    tuple(n[key] for key in ("id", "folder_id", "poi_id", "body", "created", "updated"))
                    for n in manifest["notes"]])
            with connect(docs) as con:
                for doc in manifest["documents"]:
                    con.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?)",
                                (doc["id"], doc["folder_id"], doc["trip_id"], doc["filename"],
                                 doc["title"], doc["mime"], doc["size"], doc["sha256"],
                                 doc["created"]))
                    digest = hashlib.sha256()
                    with archive.open(f"dokumente/{doc['id']}/{doc['filename']}") as source_file:
                        for index, part in enumerate(iter(lambda: source_file.read(MAX_CHUNK), b"")):
                            digest.update(part)
                            con.execute("INSERT INTO document_chunks VALUES (?,?,?)",
                                        (doc["id"], index, sqlite3.Binary(part)))
                    if digest.hexdigest() != doc["sha256"]:
                        raise ValueError("Dokument-Prüfsumme stimmt nicht")
        except Exception:
            # The two separate SQLite files cannot share an atomic transaction.
            # Restore is intentionally restricted to an empty archive; clear any
            # partial restore so a verified export can be retried.
            with connect(docs) as con:
                con.execute("DELETE FROM document_chunks")
                con.execute("DELETE FROM documents")
            with connect(main) as con:
                con.execute("DELETE FROM travel_notes")
                con.execute("DELETE FROM travel_assignments")
                con.execute("DELETE FROM travel_pois")
                con.execute("DELETE FROM travel_folders")
            raise
    return {key: len(manifest[key]) for key in ("folders", "pois", "notes", "documents")}


def _transfers(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault(STORE_KEY, {})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/search",
                                   vol.Required("query"): vol.All(str, vol.Length(min=2, max=180))})
@websocket_api.async_response
async def websocket_search(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                           msg: dict[str, Any]) -> None:
    """One explicit address search; no client-side autocomplete or location upload."""
    query = msg["query"].strip()
    if len(query) < 2:
        connection.send_error(msg["id"], "travel_search_failed", "Suchbegriff zu kurz")
        return
    state = hass.data.setdefault(DOMAIN, {}).setdefault(SEARCH_KEY, {"lock": asyncio.Lock(),
                                                                      "last": 0.0, "cache": {}})
    try:
        key = query.casefold()
        async with state["lock"]:
            cached = state["cache"].get(key)
            if cached and cached[0] > time.monotonic() - 3600:
                connection.send_result(msg["id"], {"results": cached[1]})
                return
            await asyncio.sleep(max(0.0, 1.1 - (time.monotonic() - state["last"])))
            state["last"] = time.monotonic()
            session = async_get_clientsession(hass)
            params = urlencode({"q": query, "limit": 6, "lang": "de"})
            async with session.get(f"{PHOTON_URL}?{params}", timeout=12,
                                   headers={"User-Agent": "DriveLoom/0.2.0b2 (https://github.com/lemuba/driveloom)"}) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
            results = []
            for item in data.get("features", [])[:6]:
                coords = item.get("geometry", {}).get("coordinates", [])
                props = item.get("properties", {})
                if len(coords) < 2 or not all(isinstance(n, (int, float)) and math.isfinite(n) for n in coords[:2]):
                    continue
                if abs(coords[0]) > 180 or abs(coords[1]) > 90:
                    continue
                title = str(props.get("name") or props.get("street") or props.get("city") or "Ort")
                address = ", ".join(str(props[k]) for k in ("street", "housenumber", "postcode", "city", "country")
                                    if props.get(k))
                results.append({"name": title[:160], "address": address[:300],
                                "lat": coords[1], "lon": coords[0]})
            state["cache"][key] = (time.monotonic(), results)
            if len(state["cache"]) > 200:
                state["cache"].pop(next(iter(state["cache"])))
        connection.send_result(msg["id"], {"results": results})
    except (OSError, ValueError, asyncio.TimeoutError, ClientError) as err:
        connection.send_error(msg["id"], "travel_search_failed", str(err))


def _cleanup(info: dict[str, Any]) -> None:
    try:
        Path(info["path"]).unlink(missing_ok=True)
    except OSError:
        pass


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/list"})
@websocket_api.async_response
async def websocket_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                         msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], await hass.async_add_executor_job(
        _snapshot, db_path(hass), _doc_path(hass)))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/change",
                                   vol.Required("action"): str, vol.Required("payload"): dict})
@websocket_api.async_response
async def websocket_change(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                           msg: dict[str, Any]) -> None:
    try:
        result = await hass.async_add_executor_job(_change, db_path(hass), _doc_path(hass),
                                                    msg["action"], msg["payload"])
        connection.send_result(msg["id"], result)
    except (ValueError, sqlite3.Error, OSError, TypeError) as err:
        connection.send_error(msg["id"], "travel_change_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/upload_start",
                                   vol.Required("folder_id"): str, vol.Required("filename"): str,
                                   vol.Required("size"): vol.All(int, vol.Range(min=0)),
                                   vol.Optional("mime", default="application/octet-stream"): str})
@websocket_api.async_response
async def websocket_upload_start(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                 msg: dict[str, Any]) -> None:
    try:
        folder = msg["folder_id"]
        path = db_path(hass)
        docs = _doc_path(hass)
        await hass.async_add_executor_job(_initialize, path, docs)
        def verify() -> None:
            with connect(path) as con:
                trip_id = _trip(con, folder)
                quota = con.execute("SELECT quota_bytes FROM travel_folders WHERE id=?", (trip_id,)).fetchone()[0]
            with connect(docs) as con:
                used = con.execute("SELECT COALESCE(SUM(size),0) FROM documents WHERE trip_id=?", (trip_id,)).fetchone()[0]
            if used + msg["size"] > quota:
                raise ValueError("Datei überschreitet das Gesamtvolumen der Reise")
        await hass.async_add_executor_job(verify)
        name = Path(msg["filename"].replace("\\", "/")).name[:200].strip()
        if not name:
            raise ValueError("Dateiname fehlt")
        handle, filename = await hass.async_add_executor_job(tempfile.mkstemp, "", "driveloom-upload-", str(path.parent))
        os.close(handle)
        token = uuid.uuid4().hex
        _transfers(hass)[token] = {"user": connection.user.id, "path": filename,
                                   "folder_id": folder, "filename": name, "title": name,
                                   "mime": msg["mime"][:100], "size": msg["size"],
                                   "received": 0, "sha256_hash": hashlib.sha256()}
        connection.send_result(msg["id"], {"token": token})
    except (ValueError, OSError, sqlite3.Error) as err:
        connection.send_error(msg["id"], "travel_upload_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/upload_chunk",
                                   vol.Required("token"): str, vol.Required("offset"): vol.All(int, vol.Range(min=0)),
                                   vol.Required("content"): str})
@websocket_api.async_response
async def websocket_upload_chunk(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                 msg: dict[str, Any]) -> None:
    info = _transfers(hass).get(msg["token"])
    if not info or info["user"] != connection.user.id:
        connection.send_error(msg["id"], "travel_upload_failed", "Upload nicht gefunden")
        return
    try:
        part = base64.b64decode(msg["content"], validate=True)
        if not part or len(part) > MAX_CHUNK or info["received"] != msg["offset"] or info["received"] + len(part) > info["size"]:
            raise ValueError("Ungültiger Upload-Block")
        def append() -> None:
            with Path(info["path"]).open("ab") as stream:
                stream.write(part)
        await hass.async_add_executor_job(append)
        info["sha256_hash"].update(part)
        info["received"] += len(part)
        connection.send_result(msg["id"], {"received": info["received"]})
    except (ValueError, OSError) as err:
        connection.send_error(msg["id"], "travel_upload_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/upload_finish",
                                   vol.Required("token"): str})
@websocket_api.async_response
async def websocket_upload_finish(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                  msg: dict[str, Any]) -> None:
    info = _transfers(hass).get(msg["token"])
    if not info or info["user"] != connection.user.id:
        connection.send_error(msg["id"], "travel_upload_failed", "Upload nicht gefunden")
        return
    try:
        if info["received"] != info["size"]:
            raise ValueError("Upload unvollständig")
        info["sha256"] = info["sha256_hash"].hexdigest()
        if info.get("restore"):
            result = await hass.async_add_executor_job(_restore, db_path(hass), _doc_path(hass), Path(info["path"]))
        else:
            result = await hass.async_add_executor_job(_save_document, db_path(hass), _doc_path(hass), info)
        connection.send_result(msg["id"], result)
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as err:
        connection.send_error(msg["id"], "travel_upload_failed", str(err))
    finally:
        _cleanup(info)
        _transfers(hass).pop(msg["token"], None)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/restore_start",
                                   vol.Required("size"): vol.All(int, vol.Range(min=1))})
@websocket_api.async_response
async def websocket_restore_start(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                  msg: dict[str, Any]) -> None:
    try:
        def verify() -> None:
            main, docs = db_path(hass), _doc_path(hass)
            _initialize(main, docs)
            with connect(main) as con, connect(docs) as dc:
                if any(con.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
                       for table in ("travel_folders", "travel_pois", "travel_notes", "travel_assignments")) or \
                        dc.execute("SELECT 1 FROM documents LIMIT 1").fetchone():
                    raise ValueError("Wiederherstellung nur in ein leeres Reisearchiv möglich")
        await hass.async_add_executor_job(verify)
        fd, filename = await hass.async_add_executor_job(tempfile.mkstemp, ".zip", "driveloom-restore-", str(db_path(hass).parent))
        os.close(fd)
        token = uuid.uuid4().hex
        _transfers(hass)[token] = {"user": connection.user.id, "path": filename,
                                   "size": msg["size"], "received": 0, "sha256_hash": hashlib.sha256(),
                                   "restore": True}
        connection.send_result(msg["id"], {"token": token})
    except (ValueError, OSError, sqlite3.Error) as err:
        connection.send_error(msg["id"], "travel_restore_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/document_chunk",
                                   vol.Required("document_id"): str,
                                   vol.Required("offset"): vol.All(int, vol.Range(min=0))})
@websocket_api.async_response
async def websocket_document_chunk(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                   msg: dict[str, Any]) -> None:
    try:
        connection.send_result(msg["id"], await hass.async_add_executor_job(
            _document_chunk, _doc_path(hass), msg["document_id"], msg["offset"]))
    except (ValueError, sqlite3.Error, OSError) as err:
        connection.send_error(msg["id"], "travel_download_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/export_start",
                                   vol.Optional("folder_id", default=""): str})
@websocket_api.async_response
async def websocket_export_start(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                 msg: dict[str, Any]) -> None:
    token = uuid.uuid4().hex
    fd, filename = await hass.async_add_executor_job(tempfile.mkstemp, ".zip", "driveloom-export-", str(db_path(hass).parent))
    os.close(fd)
    try:
        size = await hass.async_add_executor_job(_export, db_path(hass), _doc_path(hass),
                                                  Path(filename), msg["folder_id"])
        _transfers(hass)[token] = {"user": connection.user.id, "path": filename,
                                   "size": size, "created": time.time(), "export": True}
        connection.send_result(msg["id"], {"token": token, "size": size})
    except (ValueError, OSError, sqlite3.Error) as err:
        Path(filename).unlink(missing_ok=True)
        connection.send_error(msg["id"], "travel_export_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/travel/export_chunk",
                                   vol.Required("token"): str,
                                   vol.Required("offset"): vol.All(int, vol.Range(min=0))})
@websocket_api.async_response
async def websocket_export_chunk(hass: HomeAssistant, connection: websocket_api.ActiveConnection,
                                 msg: dict[str, Any]) -> None:
    info = _transfers(hass).get(msg["token"])
    if not info or not info.get("export") or info["user"] != connection.user.id:
        connection.send_error(msg["id"], "travel_export_failed", "Export nicht gefunden")
        return
    try:
        def read() -> bytes:
            with Path(info["path"]).open("rb") as source:
                source.seek(msg["offset"])
                return source.read(MAX_CHUNK)
        part = await hass.async_add_executor_job(read)
        connection.send_result(msg["id"], {"size": info["size"], "content": base64.b64encode(part).decode("ascii")})
        if msg["offset"] + len(part) >= info["size"]:
            _cleanup(info)
            _transfers(hass).pop(msg["token"], None)
    except OSError as err:
        connection.send_error(msg["id"], "travel_export_failed", str(err))


def async_register_websocket(hass: HomeAssistant) -> None:
    for command in (websocket_list, websocket_change, websocket_search, websocket_upload_start,
                    websocket_upload_chunk, websocket_upload_finish, websocket_restore_start,
                    websocket_document_chunk, websocket_export_start, websocket_export_chunk):
        websocket_api.async_register_command(hass, command)
