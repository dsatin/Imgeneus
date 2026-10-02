#!/usr/bin/env python3
"""Catalog verified client resources and decode bounded media/map metadata."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct

from archive import FormatError, sha256_file, target_path, write_json
from sdata import preserve_output
from tables import TableReader

TOOL_VERSION = "1.0.0"


def parse_zon(data):
    reader = TableReader(data)
    tag = reader.number()
    if tag != 5:
        raise FormatError(f"Unverified ZON format tag: {tag}")
    count = reader.count(65)
    rows = [reader.record(i, "BBB" + "I" * 14 + "H", 1, strings_first=False)
            for i in range(count)]
    reader.finish()
    return rows, {"format_tag": tag, "declared_records": count,
                  "bytes_consumed": len(data), "structured_round_trip_matches": True,
                  "semantic_status": "unknown"}


def parse_world_config(data):
    lines, sections, current = [], [], None
    offset = 0
    for ordinal, raw in enumerate(data.splitlines(keepends=True)):
        body = raw.rstrip(b"\r\n")
        stripped = body.strip()
        row = {"ordinal": ordinal, "offset": offset, "size_bytes": len(raw),
               "raw_hex": raw.hex(), "kind": "unknown"}
        if not stripped:
            row["kind"] = "blank"
        elif stripped.startswith(b"#"):
            row["kind"] = "comment"
        elif re.fullmatch(rb"\[[A-Za-z0-9_-]+\]", stripped):
            row["kind"] = "section"
            current = {"section": stripped[1:-1].decode("ascii"), "offset": offset, "fields": []}
            sections.append(current)
        elif b"=" in stripped and current is not None:
            key, value = stripped.split(b"=", 1)
            if key.isascii():
                row["kind"] = "field"
                field = {"key": key.decode("ascii"), "raw_value_hex": value.hex(), "offset": offset,
                         "text": value.decode("ascii") if value.isascii() else None,
                         "integer_candidate": int(value, 10) if re.fullmatch(rb"[+-]?[0-9]+", value) else None,
                         "semantic_status": "unknown"}
                current["fields"].append(field)
        lines.append(row)
        offset += len(raw)
    if b"".join(bytes.fromhex(row["raw_hex"]) for row in lines) != data:
        raise FormatError("WorldMap.cfg reconstruction differs from source")
    return lines, sections


def wave_metadata(stream, size, odd_chunk_padding=True):
    start = stream.read(12)
    if len(start) != 12 or start[:4] != b"RIFF" or start[8:] != b"WAVE":
        raise FormatError("Invalid RIFF/WAVE header")
    declared = struct.unpack_from("<I", start, 4)[0] + 8
    if declared != size:
        raise FormatError(f"RIFF extent differs from file size: {declared} vs {size}")
    chunks, formats, audio_bytes = [], [], 0
    position = 12
    while position < size:
        stream.seek(position)
        header = stream.read(8)
        if len(header) != 8:
            raise FormatError("Truncated RIFF chunk header")
        length = struct.unpack_from("<I", header, 4)[0]
        end = position + 8 + length
        padding = length % 2 if odd_chunk_padding else 0
        if end + padding > size:
            raise FormatError("RIFF chunk exceeds file bounds")
        chunks.append({"tag_hex": header[:4].hex(), "offset": position, "size_bytes": length})
        if header[:4] == b"fmt ":
            if length < 16:
                raise FormatError("Truncated WAVE format chunk")
            raw = stream.read(length)
            values = struct.unpack_from("<HHIIHH", raw)
            formats.append({**dict(zip(("format_tag", "channels", "sample_rate_hz", "byte_rate",
                                        "block_alignment", "bits_per_sample"), values)),
                            "offset": position + 8, "raw_hex": raw.hex(),
                            "unknown_extension_hex": raw[16:].hex()})
        if header[:4] == b"data":
            audio_bytes += length
        position = end + padding
    if not formats:
        raise FormatError("RIFF/WAVE has no format chunk")
    return {"kind": "wave", "formats": formats, "chunks": chunks,
            "layout_variant": "riff_padded_chunks" if odd_chunk_padding else "observed_unpadded_chunks",
            "audio_data_bytes": audio_bytes, "payload_decode_status": "unknown"}


def metadata(path, extension):
    size = path.stat().st_size
    with path.open("rb") as stream:
        head = stream.read(128)
        if head[:4] == b"DDS ":
            if len(head) < 128 or struct.unpack_from("<I", head, 4)[0] != 124:
                raise FormatError("Invalid DDS header extent")
            height, width = struct.unpack_from("<II", head, 12)
            if not width or not height or struct.unpack_from("<I", head, 76)[0] != 32:
                raise FormatError("Invalid DDS dimensions/pixel format extent")
            return {"kind": "dds", "width": width, "height": height,
                    "mipmap_count_raw": struct.unpack_from("<I", head, 28)[0],
                    "fourcc_hex": head[84:88].hex(), "header_hex": head.hex(),
                    "payload_decode_status": "unknown"}
        if head[:2] == b"BM":
            if len(head) < 54 or struct.unpack_from("<I", head, 14)[0] < 40:
                raise FormatError("Unverified/truncated BMP header variant")
            width, height = struct.unpack_from("<ii", head, 18)
            if width <= 0 or not height:
                raise FormatError("Invalid BMP dimensions")
            return {"kind": "bmp", "width": width, "height_raw_i32": height,
                    "bits_per_pixel": struct.unpack_from("<H", head, 28)[0],
                    "header_hex": head[:54].hex(), "payload_decode_status": "unknown"}
        if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
            stream.seek(0)
            try:
                return wave_metadata(stream, size)
            except FormatError as strict_error:
                # Two verified sample files omit padding after odd data chunks.
                # Only accept this explicit variant if the entire chunk tree fits.
                stream.seek(0)
                result = wave_metadata(stream, size, odd_chunk_padding=False)
                result["standard_layout_error"] = str(strict_error)
                result["identification_status"] = "inferred"
                return result
        if extension == ".tga":
            if len(head) < 18:
                raise FormatError("Truncated candidate TGA header")
            width, height = struct.unpack_from("<HH", head, 12)
            if head[1] not in (0, 1) or head[2] not in (1, 2, 3, 9, 10, 11) or not width or not height:
                raise FormatError("Unverified candidate TGA structure")
            return {"kind": "tga_candidate", "width": width, "height": height,
                    "image_type_raw": head[2], "pixel_depth_raw": head[16],
                    "descriptor_raw": head[17], "header_hex": head[:18].hex(),
                    "identification_status": "inferred", "payload_decode_status": "unknown"}
        if extension == ".wld" and head[:4] in (b"FLD\0", b"DUN\0"):
            result = {"kind": "wld_header", "signature_hex": head[:4].hex(),
                      "payload_decode_status": "unknown"}
            if head[:4] == b"FLD\0":
                if len(head) < 8:
                    raise FormatError("Truncated FLD header")
                result["unknown_header_i32"] = struct.unpack_from("<i", head, 4)[0]
            return result
    return {"kind": "opaque", "prefix_hex": head[:32].hex(), "payload_decode_status": "unknown",
            "pending_reason": "No reader implemented for this source signature/structure"}


def run(args):
    if not re.fullmatch(r"[0-9a-f]{64}", args.executable_sha256):
        raise FormatError("Expected a lowercase SHA-256 executable identifier")
    manifest_hash = sha256_file(args.manifest)
    extraction = json.loads(args.extraction_report.read_text())
    if extraction["manifest"]["sha256"] != manifest_hash:
        raise FormatError("Archive manifest hash differs from extraction report")
    root = args.extracted_root.resolve()
    protected = [root, root.parent / "originals", root.parent / "decoded"]
    for output in (args.output_dir.resolve(), args.report.resolve()):
        if any(output == source or source in output.parents for source in protected):
            raise FormatError("Resource outputs must be outside client source directories")
    catalogs, maps, errors = [], [], []
    with args.manifest.open(encoding="utf-8") as stream:
        for line in stream:
            entry = json.loads(line)
            if entry["baseline_id"] != extraction["baseline_id"]:
                raise FormatError("Entry baseline differs from extraction report")
            row = {"id": entry["id"], "baseline_id": entry["baseline_id"],
                   "source_path": entry["original_path"], "entry_kind": entry["entry_kind"],
                   "source_sha256": entry["content"]["sha256"], "size_bytes": entry["size_bytes"],
                   "saf_offset": entry["saf_offset"], "extension": entry["extension"],
                   "domain_hint": entry["domain_hint"], "classification_status": "inferred",
                   "schema_id": "EP45-A3-RESOURCE-001", "status": "inventoried",
                   "semantic_status": "unknown"}
            try:
                if entry["content"]["status"] != "extracted":
                    raise FormatError("Entry was not successfully extracted")
                path = target_path(root, entry["extracted_path"])
                if path.stat().st_size != entry["size_bytes"] or sha256_file(path) != row["source_sha256"]:
                    raise FormatError("Extracted resource size/hash mismatch")
                row["metadata"] = metadata(path, entry["extension"])
                row["integrity_status"] = "statically_validated"
                row["header_status"] = "decoded" if row["metadata"]["kind"] != "opaque" else "unknown"
                if entry["original_path"] == "world/TacticsZone.zon":
                    records, header = parse_zon(path.read_bytes())
                    row["metadata"] = {"kind": "zon", **header}
                    row["header_status"] = "decoded"
                    maps.extend({**r, "id": f"{entry['id']}:record-{r['ordinal']:06d}",
                                 "source_entry_id": entry["id"], "source_sha256": row["source_sha256"],
                                 "baseline_id": entry["baseline_id"], "schema_id": "EP45-A3-ZON-001",
                                 "status": "decoded", "semantic_status": "unknown"} for r in records)
                if entry["original_path"] == "WorldMap.cfg":
                    lines, sections = parse_world_config(path.read_bytes())
                    row["metadata"] = {"kind": "world-map-config", "line_count": len(lines),
                                       "sections": sections, "lines": lines,
                                       "structured_round_trip_matches": True}
                    row["header_status"] = "decoded"
            except (OSError, ValueError) as exc:
                row["error"] = str(exc)
                errors.append({"id": entry["id"], "path": entry["original_path"], "error": str(exc)})
            catalogs.append(row)
            if len(catalogs) % 5000 == 0:
                print(f"Verified resource entries: {len(catalogs)}", flush=True)

    def export(name, rows):
        path = target_path(args.output_dir.resolve(), name + ".jsonl")
        preserve_output(path, "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows).encode())
        return {"path": str(path), "sha256": sha256_file(path), "rows": len(rows)}

    wld_by_number = {}
    for row in catalogs:
        match = re.fullmatch(r"world/([0-9]+)\.wld", row["source_path"], flags=re.IGNORECASE)
        if match:
            wld_by_number.setdefault(int(match[1]), []).append(row["id"])
    world_map_references = []
    for row in catalogs:
        if row["source_path"] == "WorldMap.cfg" and "metadata" in row:
            for section in row["metadata"]["sections"]:
                for field in section["fields"]:
                    if field["key"] == "MapNum" and field["integer_candidate"] is not None:
                        number = field["integer_candidate"]
                        world_map_references.append({"source_entry_id": row["id"], "section": section["section"],
                                                     "offset": field["offset"], "original_value_hex": field["raw_value_hex"],
                                                     "integer_candidate": number, "target_entry_ids": wld_by_number.get(number, []),
                                                     "status": "inferred", "basis": "MapNum numeric value matches WLD filename stem; loader linkage remains unproven"})
    families = Counter(r.get("metadata", {}).get("kind", "error") for r in catalogs)
    report = {"id": "EP45-A3-RESOURCE-001", "baseline_id": extraction["baseline_id"],
              "executable_sha256": args.executable_sha256, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "tool": {"path": "tools/ep45-client/resources.py", "version": TOOL_VERSION, "sha256": sha256_file(Path(__file__))},
              "dependency_hashes": {name: sha256_file(Path(__file__).parent / name)
                                    for name in ("tables.py", "archive.py", "sdata.py")},
              "archive_manifest_sha256": manifest_hash, "extraction_report_sha256": sha256_file(args.extraction_report),
              "entries_examined": len(catalogs), "verified_entries": len(catalogs) - len(errors),
              "header_families": dict(sorted(families.items())), "errors": errors,
              "source_layout_anomalies": [{"id": r["id"], "path": r["source_path"],
                                           "layout_variant": r["metadata"]["layout_variant"],
                                           "standard_layout_error": r["metadata"]["standard_layout_error"],
                                           "runtime_playback_status": "unknown"}
                                          for r in catalogs if "standard_layout_error" in r.get("metadata", {})],
              "resource_catalog": export("resources", catalogs), "zon_catalog": export("zon", maps),
              "ui_catalog": export("ui-resources", [r for r in catalogs if r["domain_hint"] == "ui"]),
              "audio_catalog": export("audio-resources", [r for r in catalogs if r["domain_hint"] == "audio"]),
              "map_resource_catalog": export("map-resources", [r for r in catalogs if r["domain_hint"] == "maps" or r["source_path"] == "WorldMap.cfg"]),
              "world_map_references": world_map_references,
              "opaque_files": families["opaque"], "fully_decoded_media_payloads": 0,
              "decoded_zon_records": len(maps), "new_runtime_interactions": 0}
    write_json(args.report, report)
    print(f"Resource catalog: {len(catalogs)} entries; errors={len(errors)}; decoded ZON records={len(maps)}")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "extraction-report", "extracted-root", "output-dir", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--executable-sha256", required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
