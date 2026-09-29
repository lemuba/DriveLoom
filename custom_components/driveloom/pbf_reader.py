"""Small dependency-free streaming reader for the OSM PBF entities we index.

PBF is a sequence of compressed protobuf blocks. Decode only nodes and ways;
relations do not have a representative point in the DriveLoom catalogue.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Callable, Iterator


def _varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise ValueError("Unvollständiges PBF-Feld")
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
    raise ValueError("Ungültiges PBF-Feld")


def _fields(data: bytes) -> Iterator[tuple[int, int | bytes]]:
    offset = 0
    while offset < len(data):
        tag, offset = _varint(data, offset)
        number, kind = tag >> 3, tag & 7
        if not number:
            raise ValueError("Ungültiges PBF-Tag")
        if kind == 0:
            value, offset = _varint(data, offset)
        elif kind == 2:
            length, offset = _varint(data, offset)
            if length > len(data) - offset:
                raise ValueError("Abgeschnittenes PBF-Feld")
            value = data[offset:offset + length]
            offset += length
        elif kind == 1:
            offset += 8
            continue
        elif kind == 5:
            offset += 4
            continue
        else:
            raise ValueError("Unbekannter PBF-Feldtyp")
        if offset > len(data):
            raise ValueError("Abgeschnittenes PBF-Feld")
        yield number, value


def _packed(data: bytes) -> Iterator[int]:
    offset = 0
    while offset < len(data):
        value, offset = _varint(data, offset)
        yield value


def _signed(value: int) -> int:
    return (value >> 1) ^ -(value & 1)


def _delta(data: bytes) -> Iterator[int]:
    total = 0
    for value in _packed(data):
        total += _signed(value)
        yield total


def _tags(keys: list[int], values: list[int], strings: list[str]) -> dict[str, str]:
    if len(keys) != len(values):
        raise ValueError("Ungültige PBF-Tagliste")
    try:
        return {strings[key]: strings[value] for key, value in zip(keys, values)}
    except IndexError as err:
        raise ValueError("Ungültiger PBF-Stringindex") from err


def _blocks(source: Path, progress: Callable[[int], None] | None = None) -> Iterator[bytes]:
    with source.open("rb") as stream:
        while length_bytes := stream.read(4):
            if len(length_bytes) != 4:
                raise ValueError("Abgeschnittener PBF-Blockheader")
            length = struct.unpack(">I", length_bytes)[0]
            if not 0 < length <= 64 * 1024:
                raise ValueError("Ungültige PBF-Blockheadergröße")
            header = stream.read(length)
            if len(header) != length:
                raise ValueError("Abgeschnittener PBF-Blockheader")
            header_fields = dict(_fields(header))
            size = header_fields.get(3)
            if not isinstance(size, int) or not 0 < size <= 64 * 1024 * 1024:
                raise ValueError("Ungültige PBF-Blockgröße")
            blob = stream.read(size)
            if len(blob) != size:
                raise ValueError("Abgeschnittener PBF-Block")
            if progress:
                progress(stream.tell())
            blob_fields = dict(_fields(blob))
            expected = blob_fields.get(2)
            if isinstance(blob_fields.get(1), bytes):
                raw = blob_fields[1]
            elif isinstance(blob_fields.get(3), bytes):
                decompressor = zlib.decompressobj()
                raw = decompressor.decompress(blob_fields[3], 64 * 1024 * 1024 + 1)
                if decompressor.unconsumed_tail or not decompressor.eof:
                    raise ValueError("PBF-Block überschreitet 64 MiB")
                raw += decompressor.flush()
            else:
                raise ValueError("Nicht unterstützte PBF-Komprimierung")
            if len(raw) > 64 * 1024 * 1024 or expected is not None and len(raw) != expected:
                raise ValueError("Ungültige PBF-Dekomprimierung")
            if header_fields.get(1) == b"OSMData":
                yield raw


def entities(source: Path, *, nodes: bool = True, ways: bool = True,
             progress: Callable[[int], None] | None = None
             ) -> Iterator[tuple[str, int, dict[str, str], float | list[int], float | None]]:
    """Yield nodes (latitude, longitude) and tagged ways (node references)."""
    for block in _blocks(source, progress):
        fields = list(_fields(block))
        strings = [value.decode("utf-8", "replace")
                   for number, table in fields if number == 1
                   for field, value in _fields(table) if field == 1]
        scalars = {number: value for number, value in fields if isinstance(value, int)}
        granularity = scalars.get(17, 100)
        lat_offset, lon_offset = scalars.get(19, 0), scalars.get(20, 0)

        def coordinate(raw: int, offset: int) -> float:
            return (offset + granularity * raw) * 1e-9

        for number, group in fields:
            if number != 2:
                continue
            for kind, entity in _fields(group):
                if nodes and kind == 1:  # uncompressed Node
                    node_fields = list(_fields(entity))
                    scalar = {key: value for key, value in node_fields if isinstance(value, int)}
                    keys = [x for key, data in node_fields if key == 2 for x in _packed(data)]
                    vals = [x for key, data in node_fields if key == 3 for x in _packed(data)]
                    yield ("node", _signed(scalar[1]), _tags(keys, vals, strings),
                           coordinate(_signed(scalar[8]), lat_offset),
                           coordinate(_signed(scalar[9]), lon_offset))
                elif nodes and kind == 2:  # DenseNodes: delta encoded coordinates
                    dense = dict(_fields(entity))
                    ids = _delta(dense[1])
                    lats = _delta(dense[8])
                    lons = _delta(dense[9])
                    tags = iter(_packed(dense.get(10, b"")))
                    for osm_id, lat, lon in zip(ids, lats, lons):
                        decoded = {}
                        for key in tags:
                            if key == 0:
                                break
                            try:
                                decoded[strings[key]] = strings[next(tags)]
                            except (IndexError, StopIteration) as err:
                                raise ValueError("Ungültige PBF-Dense-Tagliste") from err
                        yield ("node", osm_id, decoded, coordinate(lat, lat_offset),
                               coordinate(lon, lon_offset))
                elif ways and kind == 3:
                    way_fields = list(_fields(entity))
                    scalar = {key: value for key, value in way_fields if isinstance(value, int)}
                    keys = [x for key, data in way_fields if key == 2 for x in _packed(data)]
                    vals = [x for key, data in way_fields if key == 3 for x in _packed(data)]
                    if keys:
                        refs = [ref for key, data in way_fields if key == 8
                                for ref in _delta(data)]
                        yield ("way", scalar[1], _tags(keys, vals, strings), refs, None)
