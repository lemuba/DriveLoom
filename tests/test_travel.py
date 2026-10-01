"""Exercise the beta travel store without importing a live Home Assistant server."""
import ast
import base64
import hashlib
import json
import math
import sqlite3
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tree = ast.parse((root / "custom_components/driveloom/travel.py").read_text())
functions = {"_initialize", "_tree", "_trip", "_snapshot", "_change",
             "_save_document", "_document_chunk", "_export", "_restore"}
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in functions]
namespace = {"Any": object, "Path": Path, "sqlite3": sqlite3, "time": time,
             "math": math, "uuid": uuid, "json": json, "zipfile": zipfile,
             "base64": base64, "hashlib": hashlib, "MAX_CHUNK": 256 * 1024,
             "connect": __import__("sqlite3").connect}

def connect(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

namespace["connect"] = connect
exec(compile(ast.Module(body=selected, type_ignores=[]), "<travel>", "exec"), namespace)
change = namespace["_change"]
snapshot = namespace["_snapshot"]

with tempfile.TemporaryDirectory() as temp:
    main, docs = Path(temp) / "driveloom.db", Path(temp) / "driveloom-documents.db"
    year = change(main, docs, "folder_save", {"name": "2027"})["id"]
    month = change(main, docs, "folder_save", {"name": "Juni", "parent_id": year})["id"]
    trip = change(main, docs, "folder_save", {"name": "Estland", "parent_id": month,
                                                     "kind": "trip", "quota_mb": 1})["id"]
    other = change(main, docs, "folder_save", {"name": "Deutschland", "kind": "trip"})["id"]
    try:
        change(main, docs, "folder_save", {"id": year, "name": "2027", "parent_id": trip})
        raise AssertionError("recursive folder move accepted")
    except ValueError:
        pass
    poi = change(main, docs, "poi_save", {"name": "Hafen", "lat": 59.43, "lon": 24.75,
            "source": "OSM", "source_id": "node/123", "metadata": {"website": "https://example.org"}})["id"]
    change(main, docs, "assign", {"folder_id": trip, "poi_id": poi})
    change(main, docs, "assign", {"folder_id": other, "poi_id": poi})
    for text in ("Pass mitnehmen", "Öffnungszeiten prüfen"):
        change(main, docs, "note_save", {"folder_id": trip, "body": text})
    data = snapshot(main, docs)
    assert len(data["assignments"]) == 2 and len(data["notes"]) == 2
    assert data["pois"][0]["metadata"]["website"] == "https://example.org"
    file = Path(temp) / "beleg.pdf"
    file.write_bytes(b"%PDF" + b"A" * (900 * 1024))
    upload = {"path": str(file), "folder_id": trip, "filename": "beleg.pdf", "title": "Beleg",
              "mime": "application/pdf", "size": file.stat().st_size,
              "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
    doc_id = namespace["_save_document"](main, docs, upload)["id"]
    chunks = []
    for offset in range(0, upload["size"], 256 * 1024):
        chunks.append(base64.b64decode(namespace["_document_chunk"](docs, doc_id, offset)["content"]))
    assert b"".join(chunks) == file.read_bytes()
    try:
        namespace["_save_document"](main, docs, upload)
        raise AssertionError("per-trip quota ignored")
    except ValueError:
        pass
    export = Path(temp) / "export.zip"
    namespace["_export"](main, docs, export, trip)
    with zipfile.ZipFile(export) as z:
        manifest = json.loads(z.read("reise.json"))
        assert len(manifest["documents"]) == 1 and len(manifest["notes"]) == 2
        assert len(manifest["pois"]) == 1 and len(manifest["assignments"]) == 1
        assert [f["name"] for f in manifest["folders"]] == ["2027", "Juni", "Estland"]
        assert z.read(f"dokumente/{doc_id}/beleg.pdf") == file.read_bytes()
    restored_main, restored_docs = Path(temp) / "restore.db", Path(temp) / "restore-docs.db"
    assert namespace["_restore"](restored_main, restored_docs, export)["documents"] == 1
    restored = snapshot(restored_main, restored_docs)
    assert len(restored["folders"]) == 3 and len(restored["documents"]) == 1
    assert b"".join(base64.b64decode(namespace["_document_chunk"](restored_docs, doc_id, offset)["content"])
                    for offset in range(0, upload["size"], 256 * 1024)) == file.read_bytes()
    try:
        namespace["_restore"](restored_main, restored_docs, export)
        raise AssertionError("restored twice")
    except ValueError:
        pass
    try:
        change(main, docs, "folder_save", {"id": trip, "name": "Estland", "parent_id": month,
                                            "kind": "trip", "quota_mb": 0})
        raise AssertionError("quota lowered below used")
    except ValueError:
        pass
    with zipfile.ZipFile(export) as z, zipfile.ZipFile(Path(temp) / "corrupt.zip", "w") as bad:
        for entry in z.infolist():
            content = z.read(entry.filename)
            bad.writestr(entry.filename, b"?" * len(content) if entry.filename.endswith("beleg.pdf") else content)
    corrupt_main, corrupt_docs = Path(temp) / "corrupt.db", Path(temp) / "corrupt-docs.db"
    try:
        namespace["_restore"](corrupt_main, corrupt_docs, Path(temp) / "corrupt.zip")
        raise AssertionError("corrupt archive restored")
    except ValueError:
        assert snapshot(corrupt_main, corrupt_docs)["folders"] == []
    within = change(main, docs, "folder_save", {"name": "Unterlagen", "kind": "folder", "parent_id": trip})["id"]
    inner_upload = {**upload, "folder_id": within}
    change(main, docs, "quota", {"folder_id": trip, "quota_mb": 2})
    inner_id = namespace["_save_document"](main, docs, inner_upload)["id"]
    try:
        change(main, docs, "folder_save", {"id": trip, "name": "Estland", "parent_id": month,
                                            "kind": "trip", "quota_mb": 1})
        raise AssertionError("folder update lowered quota below used")
    except ValueError:
        pass
    change(main, docs, "folder_save", {"id": within, "name": "Unterlagen", "kind": "folder",
                                        "parent_id": other})
    assert next(d for d in snapshot(main, docs)["documents"] if d["id"] == inner_id)["trip_id"] == other
    change(main, docs, "folder_save", {"id": trip, "name": "Estland", "kind": "trip",
                                        "parent_id": year, "quota_mb": 2})
    assert next(d for d in snapshot(main, docs)["documents"] if d["id"] == doc_id)["trip_id"] == trip
    change(main, docs, "folder_delete", {"id": trip})
    assert {d["id"] for d in snapshot(main, docs)["documents"]} == {inner_id}
    assert len(snapshot(main, docs)["pois"]) == 1

with tempfile.TemporaryDirectory() as temp:
    main, docs = Path(temp) / "main.db", Path(temp) / "documents.db"
    root_folder = change(main, docs, "folder_save", {"name": "2027", "quota_mb": 1})["id"]
    ordinary = change(main, docs, "folder_save", {"name": "Juni", "parent_id": root_folder})["id"]
    trip = change(main, docs, "folder_save", {"name": "Estland", "kind": "trip", "quota_mb": 1})["id"]
    file = Path(temp) / "receipt.pdf"
    file.write_bytes(b"%PDF" + b"x" * (900 * 1024))
    transfer = {"path": str(file), "folder_id": trip, "filename": file.name,
                "title": "Beleg", "mime": "application/pdf", "size": file.stat().st_size,
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
    doc_id = namespace["_save_document"](main, docs, transfer)["id"]
    change(main, docs, "document_move", {"id": doc_id, "folder_id": ordinary})
    moved = next(d for d in snapshot(main, docs)["documents"] if d["id"] == doc_id)
    assert (moved["folder_id"], moved["trip_id"]) == (ordinary, root_folder)
    assert base64.b64decode(namespace["_document_chunk"](docs, doc_id, 0)["content"]) == file.read_bytes()[:256 * 1024]
    archive = Path(temp) / "all.zip"
    namespace["_export"](main, docs, archive, "")
    reloaded_main, reloaded_docs = Path(temp) / "restored-main.db", Path(temp) / "restored-docs.db"
    assert namespace["_restore"](reloaded_main, reloaded_docs, archive)["documents"] == 1
    assert snapshot(reloaded_main, reloaded_docs)["documents"][0]["trip_id"] == root_folder
    namespace["_save_document"](main, docs, transfer)
    try:
        change(main, docs, "document_move", {"id": doc_id, "folder_id": trip})
        raise AssertionError("document move over quota accepted")
    except ValueError:
        pass
    assert next(d for d in snapshot(main, docs)["documents"] if d["id"] == doc_id)["folder_id"] == ordinary

print("PASS Reiseordner, gemeinsame POIs, Notizen, Dokumente, Quoten, Verschieben und Export")
