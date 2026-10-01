#!/usr/bin/env python3
"""Decode SData record structures, retaining unknown semantics and original bytes."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

from archive import FormatError, sha256_file, target_path, write_json
from sdata import preserve_output

TOOL_VERSION = "1.0.0"
LAYOUTS = {
    "items": "BBBBh" + "B" * 10 + "h" * 7 + "B" * 7 + "h" * 14 + "BBiihhBB",
    "mobs": "hhBiBBBiBiB" + "B" * 7 + "h",
    "kill-status": "Bih" + "Bh" * 6,
    "guild-house": "BBBBBhhhhBB",
    "cash": "iiii" + "iB" * 24,
}
SOURCE_FORMATS = {"Item/Item.SData": "items", "Monster/Monster.SData": "mobs",
                  "Character/KillStatus.SData": "kill-status",
                  "Npc/GuildHouse.SData": "guild-house", "Cash.Sdata": "cash"}


class TableReader:
    def __init__(self, data):
        self.data = data
        self.position = 0
        self.rebuilt = bytearray()

    def take(self, length):
        if length < 0 or self.position + length > len(self.data):
            raise FormatError(f"Truncated table at {self.position}: requested {length} bytes")
        value = self.data[self.position:self.position + length]
        self.position += length
        return value

    def number(self, kind="i"):
        raw = self.take(struct.calcsize("<" + kind))
        value = struct.unpack("<" + kind, raw)[0]
        self.rebuilt.extend(struct.pack("<" + kind, value))
        return value

    def count(self, minimum_record_bytes):
        value = self.number()
        if value < 0 or value > (len(self.data) - self.position) // minimum_record_bytes:
            raise FormatError(f"Invalid table count {value} at {self.position - 4}")
        return value

    def text(self):
        offset = self.position
        length = self.number()
        raw = self.take(length)
        self.rebuilt.extend(raw)
        text = None
        encoding = "unknown"
        try:
            text = raw.decode("utf-8")
            encoding = "ascii" if raw.isascii() else "utf8_candidate"
        except UnicodeDecodeError:
            pass  # Preserve undecodable bytes; never substitute replacement characters.
        terminators = len(raw) - len(raw.rstrip(b"\0"))
        return {"offset": offset, "size_bytes": length + 4, "length_raw_i32": length,
                "raw_hex": raw.hex(), "text": text.rstrip("\0") if text is not None else None,
                "encoding_status": encoding, "trailing_zero_bytes": terminators}

    def block(self, layout):
        offset = self.position
        values = [self.number(kind) for kind in layout]
        return {"offset": offset, "layout": "<" + layout, "values": values}

    def record(self, ordinal, layout, text_count=0, strings_first=True, **metadata):
        offset = self.position
        texts = [self.text() for _ in range(text_count)] if strings_first else []
        block = self.block(layout)
        if not strings_first:
            texts = [self.text() for _ in range(text_count)]
        return {"ordinal": ordinal, "offset": offset,
                "size_bytes": self.position - offset, "texts": texts,
                "numeric_blocks": [block], **metadata}

    def finish(self):
        if self.position != len(self.data):
            raise FormatError(f"Unconsumed table bytes: {len(self.data) - self.position}")
        if self.rebuilt != self.data:
            raise FormatError("Structured read/write round trip differs from source")


def parse_table(data, format_id):
    reader = TableReader(data)
    records, headers = [], {}
    layout = LAYOUTS[format_id]
    if format_id == "items":
        groups = reader.count(4)
        counts = []
        for group in range(groups):
            count = reader.count(8 + struct.calcsize("<" + layout))
            counts.append(count)
            for within_group in range(count):
                records.append(reader.record(len(records), layout, 2,
                                             group_ordinal=group, group_record_ordinal=within_group))
        headers = {"group_count": groups, "group_record_counts": counts}
    elif format_id == "guild-house":
        headers = {"unknown_header_i32": [reader.number() for _ in range(3)]}
        for ordinal in range(36):
            records.append(reader.record(ordinal, layout))
        headers["unknown_trailing_i32"] = [reader.number() for _ in range(24)]
    else:
        minimum = struct.calcsize("<" + layout) + (12 if format_id == "cash" else
                                                  4 if format_id == "mobs" else 0)
        count = reader.count(minimum)
        headers = {"declared_record_count": count}
        for ordinal in range(count):
            records.append(reader.record(ordinal, layout,
                                         3 if format_id == "cash" else 1 if format_id == "mobs" else 0,
                                         strings_first=format_id != "cash"))
    reader.finish()
    return records, headers


def numeric_fields(block):
    position = 0
    fields = {}
    for kind, value in zip(block["layout"][1:], block["values"]):
        label = {"B": "u8", "h": "i16_candidate", "i": "i32_candidate"}[kind]
        fields[f"unknown_{position:03d}_{label}"] = value
        position += struct.calcsize("<" + kind)
    return fields


def normalize(record, source, format_id):
    value = {"id": f"{source['id']}:record-{record['ordinal']:06d}",
             "domain": format_id, "baseline_id": source["baseline_id"],
             "status": "decoded", "semantic_status": "unknown",
             "client_id": None, "archive_entry_id": source["id"],
             "source_sha256": source["source_sha256"], "decoded_sha256": source["decoded_sha256"],
             "offset": record["offset"], "size_bytes": record["size_bytes"],
             "schema_id": "EP45-A2-TABLE-001", "ordinal": record["ordinal"],
             "texts": record["texts"],
             "numeric_block_offset": record["numeric_blocks"][0]["offset"] - record["offset"],
             "fields": {}}
    for block in record["numeric_blocks"]:
        value["fields"].update(numeric_fields(block))
    if format_id == "items":
        value["client_id_candidate"] = record["numeric_blocks"][0]["values"][:2]
        value["client_id_status"] = "inferred"
        value["group_ordinal"] = record["group_ordinal"]
        value["group_record_ordinal"] = record["group_record_ordinal"]
    return value


def run(container_report, output_dir, report_path):
    sources = json.loads(container_report.read_text())
    destination = output_dir.resolve()
    source_cache = Path(sources["archive_manifest_path"]).parent
    for protected in (Path(sources["executable_path"]).parent,
                      source_cache / "extracted", source_cache / "decoded"):
        for output in (destination, report_path.resolve()):
            if output == protected or protected in output.parents:
                raise FormatError("Catalog outputs must be outside client source directories")
    results = []
    for source in sources["sources"]:
        format_id = SOURCE_FORMATS.get(source["original_path"]) if source["entry_kind"] == "tree" else None
        result = {"id": source["id"], "original_path": source["original_path"],
                  "source_sha256": source["source_sha256"], "status": "unknown",
                  "format_id": format_id, "semantic_status": "unknown"}
        if not format_id:
            result["pending_reason"] = "Record layout not implemented; bytes retained in decoded cache"
            results.append(result)
            continue
        try:
            if source["status"] != "decoded":
                raise FormatError("Container has no verified decoded output")
            path = Path(source["decoded_path"])
            for output in (destination, report_path.resolve()):
                if output == path.resolve().parent or path.resolve().parent in output.parents:
                    raise FormatError("Catalog outputs must be outside decoded source directories")
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != source["decoded_sha256"]:
                raise FormatError("Decoded source hash does not match its container report")
            records, headers = parse_table(data, format_id)
            normalized = [normalize(r, source, format_id) for r in records]
            raw_path = target_path(destination, format_id + ".raw.jsonl")
            normalized_path = target_path(destination, format_id + ".jsonl")
            for target, rows in ((raw_path, records), (normalized_path, normalized)):
                output = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                                 for row in rows).encode("utf-8")
                preserve_output(target, output)
            identifier_counts = Counter(tuple(r["client_id_candidate"]) for r in normalized
                                        if "client_id_candidate" in r)
            result.update({"status": "decoded", "records": len(records),
                           "decoded_size_bytes": len(data), "bytes_consumed": len(data),
                           "structured_round_trip_matches": True, "headers": headers,
                           "raw_catalog": {"path": str(raw_path), "sha256": sha256_file(raw_path)},
                           "normalized_catalog": {"path": str(normalized_path), "sha256": sha256_file(normalized_path)},
                           "unresolved_text_encodings": sum(t["encoding_status"] == "unknown"
                                                            for r in records for t in r["texts"]),
                           "candidate_duplicate_id_groups": sum(c > 1 for c in identifier_counts.values()),
                           "candidate_group_id_mismatches": sum(r["client_id_candidate"][0] != r["group_ordinal"] + 1
                                                                 for r in normalized if "client_id_candidate" in r),
                           "first_record": normalized[0] if normalized else None,
                           "last_record": normalized[-1] if normalized else None})
        except (OSError, ValueError) as exc:
            result["error"] = str(exc)
        results.append(result)
        print(f"{source['original_path']}: {result['status']}; records={result.get('records', 0)}", flush=True)
    report = {"schema_version": 1, "baseline_id": sources["baseline_id"],
              "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "tool": {"path": "tools/ep45-client/tables.py", "version": TOOL_VERSION,
                       "sha256": sha256_file(Path(__file__))},
              "container_report_sha256": sha256_file(container_report), "sources": results,
              "active_sources": sum(s["entry_kind"] == "tree" for s in sources["sources"]),
              "structurally_decoded_formats": sum(r["status"] == "decoded" for r in results),
              "records_structurally_decoded": sum(r.get("records", 0) for r in results),
              "semantically_validated_formats": 0, "errors": sum("error" in r for r in results)}
    write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--containers", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(args.containers, args.output_dir, args.report)
        return 1 if report["errors"] else 0
    except (OSError, ValueError) as exc:
        print(f"Table error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
