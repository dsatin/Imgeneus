#!/usr/bin/env python3
"""Decode remaining SData structures without promoting candidate field meanings."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

from archive import FormatError, sha256_file, target_path, write_json
from sdata import preserve_output
from tables import TableReader

TOOL_VERSION = "1.0.0"
SCHEMA_ID = "EP45-A2-EXTENDED-001"
SKILL_LAYOUT = "BHBHHHBBBBBBBBBBBBHBBBBBBBBBBBBBBBBHHBHBBBHHBBBBBHBBBBHBHHHBHHHHHHBHBHBHHHHHHHBBBBHH"
QUEST_LAYOUT = "HH" + "B" * 10 + "HhBBBHB" + "B" * 6 + "I" * 5 + "BBHBB" + "BBB" * 3 + "BBh" + "BBB" * 3 + "BHBHB" + "BB"
RESULT_LAYOUT = "HBBBIHhBIIBBH"
FORMATS = {"Character/Skill.SData": "skills", "Monster/NpcSkill.SData": "npc-skills",
           "Npc/PriestTalk.SData": "priest-talk", "Npc/NpcQuest.Sdata": "npc-quest"}


def sequence(reader, layout):
    offset = reader.position
    count = reader.count(struct.calcsize("<" + layout))
    return {"offset": offset, "declared_count": count,
            "entries": [reader.block(layout) for _ in range(count)]}


def parse_extended(data, format_id):
    reader = TableReader(data)
    records, headers, issues, matrix = [], {}, [], []

    def record(domain, group, ordinal, blocks=None, texts=None, **extra):
        return {"domain": domain, "group_ordinal": group, "ordinal": ordinal,
                "offset": reader.position, "numeric_blocks": blocks or [],
                "texts": texts or [], **extra}

    def append(row):
        row["size_bytes"] = reader.position - row["offset"]
        records.append(row)

    if format_id in ("skills", "npc-skills"):
        groups = reader.number()
        # The client allocates nine slots per group. A group must have at least
        # one complete record; missing terminal slots are reported separately.
        if groups < 0 or groups > (len(data) - 4) // 124:
            raise FormatError("Invalid skill group count")
        headers = {"declared_group_count": groups, "records_per_group": 9,
                   "expected_records": groups * 9}
        for ordinal in range(groups * 9):
            if reader.position == len(data):
                issues.append({"id": "missing-terminal-records", "offset": reader.position,
                               "expected_records": groups * 9, "complete_records": ordinal,
                               "missing_records": groups * 9 - ordinal})
                break
            row = record(format_id, ordinal // 9, ordinal,
                         group_record_ordinal=ordinal % 9)
            row["texts"] = [reader.text(), reader.text()]
            row["numeric_blocks"] = [reader.block(SKILL_LAYOUT)]
            append(row)
    elif format_id == "priest-talk":
        headers["section_counts"] = []
        headers["section_count_offsets"] = []
        for group in range(4):
            headers["section_count_offsets"].append(reader.position)
            count = reader.count(9)
            headers["section_counts"].append(count)
            for ordinal in range(count):
                row = record(format_id, group, ordinal)
                row["numeric_blocks"] = [reader.block("B")]
                row["texts"] = [reader.text(), reader.text()]
                append(row)
    elif format_id == "npc-quest":
        headers["npc_group_counts"] = []
        headers["npc_group_count_offsets"] = []
        for group in range(13):
            headers["npc_group_count_offsets"].append(reader.position)
            count = reader.count(35 + (5 if group == 0 else 66 if group == 1 else 0))
            headers["npc_group_counts"].append(count)
            for ordinal in range(count):
                row = record("npcs", group, ordinal)
                row["numeric_blocks"] = [reader.block("BH" + ("B" if group == 0 else "") + "IIII")]
                row["texts"] = [reader.text(), reader.text()]
                if group == 0:
                    row["unknown_pairs"] = sequence(reader, "BB")
                if group == 1:
                    row["unknown_targets"] = []
                    for _ in range(3):
                        # Keep float candidates as bits, including NaN payloads.
                        row["unknown_targets"].append({"numeric_blocks": [reader.block("HIII")],
                                                       "texts": [reader.text()],
                                                       "trailing_block": reader.block("I")})
                row["unknown_lists"] = [sequence(reader, "H"), sequence(reader, "H")]
                append(row)
        matrix_offset = reader.position
        for cell in range(65536):
            for slot in range(2):
                array = sequence(reader, "H")
                if array["declared_count"]:
                    matrix.append({"cell_ordinal": cell, "list_ordinal": slot, **array})
        headers["matrix"] = {"offset": matrix_offset,
                             "size_bytes": reader.position - matrix_offset,
                             "cells": 65536, "arrays": 131072,
                             "nonempty_arrays": len(matrix),
                             "sha256": hashlib.sha256(data[matrix_offset:reader.position]).hexdigest()}
        headers["quest_count_offset"] = reader.position
        count = reader.count(203)
        headers["quest_count"] = count
        for ordinal in range(count):
            row = record("quests", 0, ordinal)
            row["numeric_blocks"] = [reader.block("H")]
            row["texts"] = [reader.text(), reader.text()]
            row["numeric_blocks"].append(reader.block(QUEST_LAYOUT))
            row["unknown_results"] = [reader.block(RESULT_LAYOUT) for _ in range(3)]
            row["texts"].extend(reader.text() for _ in range(7))
            append(row)
    else:
        raise FormatError(f"Unsupported extended format: {format_id}")
    reader.finish()
    return records, headers, issues, matrix


def normalize(row, source):
    # Retain block boundaries and nested arrays: offsets alone are field IDs.
    return {**row, "id": f"{source['id']}:{row['domain']}:group-{row['group_ordinal']:03d}:record-{row['ordinal']:06d}",
            "baseline_id": source["baseline_id"], "archive_entry_id": source["id"],
            "source_path": source["original_path"], "source_sha256": source["source_sha256"],
            "decoded_sha256": source["decoded_sha256"], "schema_id": SCHEMA_ID,
            "status": "decoded", "semantic_status": "unknown", "client_id": None}


def unresolved_texts(value):
    if isinstance(value, dict):
        return (int(value.get("encoding_status") == "unknown")
                + sum(unresolved_texts(v) for v in value.values()))
    if isinstance(value, list):
        return sum(unresolved_texts(v) for v in value)
    return 0


def run(containers, output_dir, report_path):
    report = json.loads(containers.read_text())
    protected = [Path(report["executable_path"]).resolve().parent]
    cache = Path(report["archive_manifest_path"]).resolve().parent
    protected += [cache / "decoded", cache / "extracted"]
    for destination in (output_dir.resolve(), report_path.resolve()):
        if any(destination == root or root in destination.parents for root in protected):
            raise FormatError("Outputs must be outside client source directories")
    results = []
    for source in report["sources"]:
        format_id = FORMATS.get(source["original_path"])
        if source["entry_kind"] == "supplemental" and source["original_path"] == "Skill.SData":
            format_id = "skills"
        if not format_id:
            continue  # This report covers only the explicitly listed extended formats.
        result = {"id": source["id"], "entry_kind": source["entry_kind"],
                  "original_path": source["original_path"], "format_id": format_id,
                  "source_sha256": source["source_sha256"], "decoded_sha256": source.get("decoded_sha256"),
                  "status": "unknown", "semantic_status": "unknown"}
        try:
            if source["status"] != "decoded":
                raise FormatError("Source container is not decoded")
            path = Path(source["decoded_path"])
            for destination in (output_dir.resolve(), report_path.resolve()):
                if path.resolve().parent == destination or path.resolve().parent in destination.parents:
                    raise FormatError("Outputs must be outside decoded source directories")
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != source["decoded_sha256"]:
                raise FormatError("Decoded source hash mismatch")
            rows, headers, issues, matrix = parse_extended(data, format_id)
            exports = {}
            for label, values in (("raw", rows), ("normalized", [normalize(r, source) for r in rows]),
                                  ("matrix", matrix)):
                if label == "matrix" and format_id != "npc-quest":
                    continue
                target = target_path(output_dir.resolve(), f"{source['id']}.{label}.jsonl")
                payload = "".join(json.dumps(v, ensure_ascii=False, separators=(",", ":")) + "\n"
                                  for v in values).encode("utf-8")
                preserve_output(target, payload)
                exports[label] = {"path": str(target), "sha256": sha256_file(target), "rows": len(values)}
            result.update({"status": "unknown" if issues else "decoded", "issues": issues,
                           "complete_records": len(rows), "headers": headers, "exports": exports,
                           "bytes_consumed": len(data), "structured_round_trip_matches": True,
                           "domain_counts": {d: sum(r["domain"] == d for r in rows)
                                             for d in sorted({r["domain"] for r in rows})},
                           "unresolved_text_encodings": unresolved_texts(rows),
                           "first_record": rows[0] if rows else None,
                           "last_record": rows[-1] if rows else None})
        except (OSError, ValueError) as exc:
            result["error"] = str(exc)
        results.append(result)
        print(f"{source['id']}: {result['status']}; complete records={result.get('complete_records', 0)}", flush=True)
    output = {"schema_version": 1, "schema_id": SCHEMA_ID,
              "baseline_id": report["baseline_id"], "executable_sha256": report["executable_sha256"],
              "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "tool": {"path": "tools/ep45-client/extended_tables.py", "version": TOOL_VERSION,
                       "sha256": sha256_file(Path(__file__))},
              "dependency_hashes": {name: sha256_file(Path(__file__).parent / name)
                                    for name in ("tables.py", "archive.py", "sdata.py")},
              "container_report_sha256": sha256_file(containers), "sources": results,
              "active_sources_in_scope": sum(r["entry_kind"] == "tree" for r in results),
              "active_sources_fully_decoded": sum(r["entry_kind"] == "tree" and r["status"] == "decoded" for r in results),
              "sources_with_issues": sum(bool(r.get("issues") or r.get("error")) for r in results),
              "semantically_validated_formats": 0}
    write_json(report_path, output)
    return 1 if output["sources_with_issues"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--containers", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    return run(args.containers, args.output_dir, args.report)


if __name__ == "__main__":
    raise SystemExit(main())
