#!/usr/bin/env python3
"""Audit remaining table gaps and export separately evidenced lookup keys."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from archive import FormatError, sha256_file, target_path, write_json
from sdata import preserve_output
from tables import TableReader

TOOL_VERSION = "1.0.0"


def verified_jsonl(export):
    path = Path(export["path"])
    if sha256_file(path) != export["sha256"]:
        raise FormatError(f"Catalog hash mismatch: {path}")
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def compare_skills(active, supplemental):
    changes = []
    for ordinal, (left, right) in enumerate(zip(active, supplemental)):
        left_values = left["numeric_blocks"][0]["values"]
        right_values = right["numeric_blocks"][0]["values"]
        text_equal = [t["raw_hex"] for t in left["texts"]] == [t["raw_hex"] for t in right["texts"]]
        if not text_equal or left_values != right_values:
            changes.append({"record_ordinal": ordinal, "group_ordinal": left["group_ordinal"],
                            "group_record_ordinal": left["group_record_ordinal"],
                            "active_offset": left["offset"], "supplemental_offset": right["offset"],
                            "text_bytes_equal": text_equal,
                            "different_numeric_field_ordinals": [i for i, (a, b) in enumerate(zip(left_values, right_values)) if a != b]})
    return {"shared_records": min(len(active), len(supplemental)),
            "equal_content_records": min(len(active), len(supplemental)) - len(changes),
            "changed_content_records": len(changes), "changes": changes,
            "additional_supplemental_records": max(0, len(supplemental) - len(active)),
            "active_usage_of_supplemental": "unknown"}


def texts(value):
    if isinstance(value, dict):
        if "encoding_status" in value and "raw_hex" in value:
            yield value
        else:
            for child in value.values():
                yield from texts(child)
    elif isinstance(value, list):
        for child in value:
            yield from texts(child)


def encoding_candidates(rows):
    unresolved = [bytes.fromhex(t["raw_hex"]) for t in texts(rows) if t["encoding_status"] == "unknown"]
    candidates = {}
    for encoding in ("cp949", "cp1252", "utf-16le"):
        matches = 0
        for raw in unresolved:
            try:
                matches += raw.decode(encoding).encode(encoding) == raw
            except UnicodeError:
                pass
        candidates[encoding] = {"lossless_texts": matches, "tested_texts": len(unresolved), "status": "inferred"}
    return {"unresolved_texts": len(unresolved), "candidates": candidates,
            "client_conversion_encoding": "unknown"}


def parse_guild_house(data):
    reader = TableReader(data)
    headers = {"unknown_header_i32": [reader.number() for _ in range(3)]}
    rows = [reader.record(i, "BBBBBHHHHH") for i in range(36)]
    headers["unknown_trailing_i32"] = [reader.number() for _ in range(24)]
    reader.finish()
    return rows, headers


def lookup_key(row, domain):
    if domain == "mobs":
        return {"index_u16": row["ordinal"]}
    if domain == "items":
        return {"group_u8": row["group_ordinal"] + 1,
                "record_u8": row["group_record_ordinal"] + 1}
    return {"group_u16": row["group_ordinal"] + 1,
            "slot_u8": row["group_record_ordinal"] + 1}


def run(args):
    containers = json.loads(args.containers.read_text())
    initial = json.loads(args.initial.read_text())
    extended = json.loads(args.extended.read_text())
    profile = json.loads(args.profile.read_text())
    if sha256_file(args.executable) != profile["executable_sha256"]:
        raise FormatError("Executable hash differs from analyzed lookup profile")
    if any(r["baseline_id"] != profile["baseline_id"] for r in (containers, initial, extended)):
        raise FormatError("Report baselines differ")
    protected = [args.executable.resolve().parent]
    cache = Path(containers["archive_manifest_path"]).resolve().parent
    protected += [cache / "originals", cache / "decoded", cache / "extracted"]
    for output in (args.output_dir.resolve(), args.report.resolve()):
        if any(output == root or root in output.parents for root in protected):
            raise FormatError("Audit outputs must be outside original/decoded/extracted sources")
    executable = args.executable.read_bytes()
    for window in profile["windows"]:
        start = window["file_offset"]
        if hashlib.sha256(executable[start:start + window["size_bytes"]]).hexdigest() != window["source_bytes_sha256"]:
            raise FormatError("Lookup instruction window hash mismatch")

    def export(name, rows):
        path = target_path(args.output_dir.resolve(), name + ".jsonl")
        preserve_output(path, "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows).encode())
        return {"path": str(path), "sha256": sha256_file(path), "rows": len(rows)}

    keyed, encodings = [], []
    for report in (initial, extended):
        for source in report["sources"]:
            if "normalized_catalog" in source:
                rows = verified_jsonl(source["normalized_catalog"])
            elif "exports" in source:
                rows = verified_jsonl(source["exports"]["normalized"])
            else:
                continue
            encodings.append({"id": source["id"], **encoding_candidates(rows)})
            domain = source["format_id"]
            if domain not in ("items", "mobs", "skills", "npc-skills"):
                continue
            values = [{**row, "source_record_schema_id": row["schema_id"], "schema_id": "EP45-A2-LOOKUP-001",
                       "client_lookup_key": lookup_key(row, domain),
                       "lookup_status": "statically_validated", "lookup_evidence_id": f"EP45-A2-LOOKUP-{domain.upper()}",
                       "lookup_limitations": "Static address selection; protocol ID meaning and runtime behavior remain unvalidated"} for row in rows]
            entry = {"id": source["id"], "entry_kind": source.get("entry_kind", "tree"),
                     "domain": domain, "source_status": source["status"],
                     "key_count": len(values), "export": export(source["id"] + ".lookup", values)}
            if domain == "items":
                entry["stored_pair_matches_lookup_key"] = sum(row["client_id_candidate"] == list(value["client_lookup_key"].values()) for row, value in zip(rows, values))
            if domain in ("skills", "npc-skills"):
                entry["first_numeric_byte_distribution"] = dict(sorted(Counter(row["numeric_blocks"][0]["values"][0] for row in rows).items()))
            keyed.append(entry)
    sources = {s["id"]: s for s in extended["sources"]}
    active = verified_jsonl(sources["tree-000013"]["exports"]["raw"])
    supplemental = verified_jsonl(sources["supplemental-000002"]["exports"]["raw"])
    comparison = compare_skills(active, supplemental)
    changes = comparison.pop("changes")
    comparison["difference_export"] = export("skill-source-differences", changes)
    guild = next(s for s in containers["sources"] if s["original_path"] == "Npc/GuildHouse.SData" and s["entry_kind"] == "tree")
    if sha256_file(Path(guild["decoded_path"])) != guild["decoded_sha256"]:
        raise FormatError("Guild-house decoded hash mismatch")
    rows, headers = parse_guild_house(Path(guild["decoded_path"]).read_bytes())
    corrected = [{**row, "id": f"{guild['id']}:record-{row['ordinal']:06d}",
                  "baseline_id": guild["baseline_id"], "source_sha256": guild["source_sha256"],
                  "decoded_sha256": guild["decoded_sha256"], "schema_id": "EP45-A2-GUILD-002",
                  "status": "decoded", "semantic_status": "unknown"} for row in rows]
    report = {"id": "EP45-A2-AUDIT-001", "baseline_id": profile["baseline_id"],
              "executable_sha256": profile["executable_sha256"], "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "tool": {"path": "tools/ep45-client/a2_audit.py", "version": TOOL_VERSION, "sha256": sha256_file(Path(__file__))},
              "input_hashes": {name: sha256_file(getattr(args, name)) for name in ("initial", "extended", "containers", "profile")},
              "lookup_catalogs": keyed, "skill_source_comparison": comparison,
              "encoding_analysis": encodings,
              "guild_house_correction": {"id": guild["id"], "source_sha256": guild["source_sha256"],
                                        "decoded_sha256": guild["decoded_sha256"], "layout": "<BBBBBHHHHH",
                                        "headers": headers, "export": export("guild-house.corrected", corrected),
                                        "structured_round_trip_matches": True},
              "semantically_completed_formats": 0, "new_runtime_interactions": 0}
    write_json(args.report, report)
    print(f"Audited {len(keyed)} lookup catalogs; changed shared Skill records={comparison['changed_content_records']}; guild-house records={len(rows)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("containers", "initial", "extended", "profile", "executable", "output-dir", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
