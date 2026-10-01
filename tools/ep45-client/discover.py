#!/usr/bin/env python3
"""Build source/map/asset indexes; this does not decode gameplay records."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import struct

from archive import SEED_SIGNATURE, sha256_file, write_json


def reference(entry):
    return {key: entry[key] for key in
            ("id", "entry_kind", "path", "original_path", "sah_record_offset", "saf_offset", "size_bytes", "extracted_path")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--extraction-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    entries = [json.loads(line) for line in args.manifest.open(encoding="utf-8")]
    if any(e["content"]["status"] != "extraido" for e in entries):
        parser.error("Discovery requires a completely verified extraction manifest")
    metadata = {
        "schema_version": 1, "baseline_id": entries[0]["baseline_id"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool": {"path": "tools/ep45-client/discover.py", "version": "1.0.0", "sha256": sha256_file(Path(__file__))},
        "archive_manifest_sha256": sha256_file(args.manifest),
        "status": "inventariado", "gameplay_records_decoded": 0,
    }
    tables, maps, mismatches, thumbnail_caches = [], [], [], []
    for entry in entries:
        hint = entry["content"]["format_hint"]
        if entry["extension"] in (".sdata", ".cfg", ".zon"):
            item = {**reference(entry), "sha256": entry["content"]["sha256"],
                    "format_hint": hint, "domain_hint": entry["domain_hint"],
                    "record_layout_status": "desconhecido"}
            header = bytes.fromhex(entry["content"]["prefix_hex"])
            if header.startswith(SEED_SIGNATURE) and len(header) == 64:
                checksum, declared = struct.unpack_from("<II", header, 40)
                if checksum == 0:
                    checksum, declared = struct.unpack_from("<II", header, 44)
                encoded = entry["size_bytes"] - 64
                item["container_header"] = {
                    "header_size_bytes": 64, "checksum_raw_u32": checksum,
                    "declared_decoded_size_bytes": declared, "encoded_size_bytes": encoded,
                    "encoded_multiple_of_16": encoded % 16 == 0,
                    "alignment_padding_candidate_bytes": encoded - declared,
                    "decryption_validated": False,
                }
            tables.append(item)
        if entry["extension"] == ".db":
            thumbnail_caches.append({**reference(entry), "format_hint": hint,
                                     "classification": "thumbnail_cache_candidate_from_filename"})
        if entry["entry_kind"] == "tree" and entry["extension"] in (".wld", ".zon", ".svmap"):
            stem = Path(entry["path"]).stem
            maps.append({**reference(entry), "sha256": entry["content"]["sha256"],
                         "filename_numeric_id_candidate": int(stem) if stem.isdecimal() else None,
                         "id_status": "inferido_do_nome", "layout_status": "desconhecido"})
        recognized = {".dds": "dds", ".bmp": "bmp", ".wav": "wave", ".jpg": "jpeg"}
        if entry["extension"] in recognized and hint != recognized[entry["extension"]]:
            mismatches.append({**reference(entry), "extension": entry["extension"], "content_hint": hint})
    write_json(args.output_dir / "data-sources.json", {**metadata, "sources": tables})
    write_json(args.output_dir / "map-files.json", {**metadata, "files": maps,
               "wld_files": sum(e["extension"] == ".wld" for e in entries if e["entry_kind"] == "tree"),
               "svmap_files": sum(e["extension"] == ".svmap" for e in entries if e["entry_kind"] == "tree"),
               "positions_decoded": False})
    extraction_report = json.loads(args.extraction_report.read_text())
    position, gaps = 0, []
    for start, end in sorted((e["saf_offset"], e["saf_offset"] + e["size_bytes"]) for e in entries if e["size_bytes"]):
        if start > position:
            gaps.append({"offset": position, "size_bytes": start - position})
        position = max(position, end)
    if position < extraction_report["saf_size_bytes"]:
        gaps.append({"offset": position, "size_bytes": extraction_report["saf_size_bytes"] - position})
    gap_manifest = args.manifest.parent / "unreferenced-ranges.jsonl"
    with gap_manifest.open("w", encoding="utf-8") as stream:
        for gap in gaps:
            stream.write(json.dumps(gap, separators=(",", ":")) + "\n")
    write_json(args.output_dir / "asset-summary.json", {**metadata,
               "all_files": len(entries), "tree_files": sum(e["entry_kind"] == "tree" for e in entries),
               "content_hints": dict(sorted(Counter(e["content"]["format_hint"] for e in entries).items())),
               "extension_signature_disagreements": mismatches,
               "thumbnail_cache_candidates": thumbnail_caches,
               "unreferenced_saf_ranges": {"count": len(gaps), "total_size_bytes": sum(g['size_bytes'] for g in gaps),
                                           "manifest_path": str(gap_manifest), "manifest_sha256": sha256_file(gap_manifest),
                                           "semantics": "unknown; full source SAF preserved in originals"},
               "ui_files_by_extension": dict(sorted(Counter(e["extension"] for e in entries if e["domain_hint"] == "ui").items()))})
    print(f"Indexed {len(tables)} data-source candidates, {len(maps)} map files, {len(mismatches)} extension/signature disagreements; decoded gameplay records=0")


if __name__ == "__main__":
    main()
