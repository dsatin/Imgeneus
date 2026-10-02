#!/usr/bin/env python3
"""Export small verified water files and dungeon leaf spans for offline tests."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from archive import FormatError, sha256_file, target_path, write_json
from spatial import parse_dungeon, parse_water, validate_outputs

TOOL_VERSION = "1.0.0"
LEAVES = (("tree-022534", "root/3/2"), ("tree-022564", "root/3"))
SYNTHETIC_ENVELOPE = bytes(32) + b"\x01\x00\x00\x00"


def run(args):
    root = args.extracted_root.resolve()
    validate_outputs((args.output,), (root, root.parent / "originals", root.parent / "decoded",
                                     args.manifest, args.catalog_index))
    index = json.loads(args.catalog_index.read_text())
    if sha256_file(args.manifest) != index["archive_manifest_sha256"]:
        raise FormatError("Fixture manifest differs from the spatial catalog")
    entries = {e["id"]: e for e in (json.loads(line) for line in args.manifest.read_text().splitlines())}
    sources = {s["id"]: s for s in index["sources"]}
    samples = []
    selected = [(e["id"], None) for e in entries.values() if e["extension"] == ".wtr"] + list(LEAVES)
    for identifier, node_path in selected:
        entry, source = entries[identifier], sources[identifier]
        data = target_path(args.extracted_root.resolve(), entry["extracted_path"]).read_bytes()
        if (entry["baseline_id"] != index["baseline_id"] or source["source_sha256"] != entry["content"]["sha256"] or
                len(data) != entry["size_bytes"] or hashlib.sha256(data).hexdigest() != source["source_sha256"]):
            raise FormatError("Fixture source failed size/hash/baseline verification")
        offset, raw, kind = 0, data, "complete-water-file"
        if node_path is not None:
            raw_path = Path(source["raw_catalog"]["path"])
            validate_outputs((args.output,), (raw_path.parent,))
            if sha256_file(raw_path) != source["raw_catalog"]["sha256"]:
                raise FormatError("Fixture raw catalog hash mismatch")
            parts = json.loads(raw_path.read_text())["parts"]
            header = next(p for p in parts if p["section"] == "node-header" and p["node_path"] == node_path)
            flags = [p for p in parts if p["section"] == "child-present" and p["node_path"] == node_path]
            if len(flags) != 8 or any(p["value"] for p in flags):
                raise FormatError("Fixture selection is not a complete dungeon leaf")
            offset = header["offset"]
            raw = data[offset:flags[-1]["offset"] + 4]
            kind = "dungeon-leaf-in-synthetic-envelope"
        parsed = parse_water(raw) if node_path is None else parse_dungeon(SYNTHETIC_ENVELOPE + raw)
        sample = {"id": f"{identifier}:{node_path or 'complete'}", "kind": kind,
                  "archive_entry_id": identifier, "source_path": entry["original_path"],
                  "source_sha256": source["source_sha256"], "source_offset": offset,
                  "size_bytes": len(raw), "span_sha256": hashlib.sha256(raw).hexdigest(),
                  "raw_hex": raw.hex(), "expected_counts": parsed["counts"], "status": "extracted"}
        if node_path is not None:
            sample.update({"original_node_path": node_path, "synthetic_envelope_hex": SYNTHETIC_ENVELOPE.hex(),
                           "note": "Only raw_hex is extracted client evidence. The envelope is synthetic and not an original source file."})
        samples.append(sample)
    write_json(args.output, {"id": "EP45-A3-SPATIAL-FIXTURES-001", "baseline_id": index["baseline_id"],
                            "executable_sha256": index["executable_sha256"],
                            "observation_date": datetime.now(timezone.utc).date().isoformat(),
                            "tool": {"path": "tools/ep45-client/spatial_fixtures.py", "version": TOOL_VERSION,
                                     "sha256": sha256_file(Path(__file__))},
                            "samples": samples})
    print(f"Spatial source fixtures: {len(samples)}; extracted bytes={sum(s['size_bytes'] for s in samples)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "extracted-root", "catalog-index", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
