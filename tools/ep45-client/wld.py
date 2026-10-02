#!/usr/bin/env python3
"""Decode the identified client's WLD structures and catalog resource links."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

from archive import FormatError, sha256_file, target_path, write_json
from sdata import preserve_output
from tables import TableReader

TOOL_VERSION = "1.0.0"
SCHEMA_ID = "EP45-A3-WLD-001"
PLACEMENT_GROUPS = ("building", "shape", "tree", "grass", "vani0", "vani1", "dungeon", "mani")
RESOURCE_ROOTS = {"building": "entity/building", "shape": "entity/shape",
                  "tree": "entity/tree", "grass": "entity/grass",
                  "vani0": "entity/vani", "vani1": "entity/vani",
                  "dungeon": "world/dungeon", "mani": "entity/mani",
                  "object0": "entity/object", "object1": "entity/object"}


class WldReader(TableReader):
    def __init__(self, data):
        super().__init__(data)
        self.parts = []
        self.counts = {}

    def bytes(self, length):
        value = self.take(length)
        self.rebuilt.extend(value)
        return value

    def fixed_text(self, length):
        offset = self.position
        raw = self.bytes(length)
        value, separator, padding = raw.partition(b"\0")
        text, encoding = None, "unknown"
        if value.isascii():
            text, encoding = value.decode("ascii"), "ascii"
        else:
            try:
                text, encoding = value.decode("utf-8"), "utf8_candidate"
            except UnicodeDecodeError:
                pass
        return {"offset": offset, "size_bytes": length, "raw_hex": raw.hex(),
                "text": text, "encoding_status": encoding, "language": "unknown",
                "nul_terminated": bool(separator), "padding_nonzero_bytes": sum(b != 0 for b in padding)}

    def scalar(self, section, kind="i", minimum=None):
        offset = self.position
        value = self.count(minimum) if minimum is not None else self.number(kind)
        self.parts.append({"section": section, "kind": "count" if minimum is not None else "scalar",
                           "offset": offset, "size_bytes": 4, "layout": "<" + kind, "value": value})
        if minimum is not None:
            self.counts[section] = value
        return value

    def blob(self, section, length):
        offset = self.position
        raw = self.bytes(length)
        self.parts.append({"section": section, "kind": "blob", "offset": offset,
                           "size_bytes": length, "data": raw, "sha256": hashlib.sha256(raw).hexdigest(),
                           "payload_decode_status": "unknown"})

    def record(self, section, ordinal=0, fields=(), **metadata):
        offset = self.position
        texts, blocks = [], []
        for kind, width in fields:
            if kind == "text":
                texts.append(self.fixed_text(width))
            else:
                blocks.append(self.block("I" * width))
        row = {"section": section, "kind": "record", "ordinal": ordinal,
               "offset": offset, "size_bytes": self.position - offset,
               "numeric_blocks": blocks, "texts": texts, **metadata}
        self.parts.append(row)
        return row

    def array(self, section, fields, **metadata):
        width = sum(n if k == "text" else n * 4 for k, n in fields)
        count = self.scalar(section, minimum=width)
        return [self.record(section, i, fields, **metadata) for i in range(count)]

    def placements(self, group, words):
        self.array(group + "-names", (("text", 256),), resource_root=RESOURCE_ROOTS[group])
        self.array(group + "-placements", (("words", words),))


def parse_wld(data):
    reader = WldReader(data)
    reader.blob("signature", 4)
    signature = data[:4]
    if signature not in (b"DUN\0", b"FLD\0"):
        raise FormatError("Unverified WLD signature")
    extent = None
    if signature == b"FLD\0":
        extent = reader.scalar("extent")
        if extent <= 0 or extent % 2:
            raise FormatError("Unverified FLD extent; expected a positive even integer")
        samples = (extent // 2 + 1) ** 2
        # The client's 0x5a1af0 reads two grids with widths two and one.
        reader.blob("grid-u16", samples * 2)
        reader.blob("grid-u8", samples)
        reader.array("terrain-materials", (("text", 256), ("words", 1), ("text", 256)))
    reader.record("inner-resource", fields=(("text", 256),))
    for group in PLACEMENT_GROUPS:
        reader.placements(group, 11 if group == "mani" else 10)
    reader.record("effect-resource", fields=(("text", 256),))
    reader.array("effects", (("words", 10),))
    reader.placements("object0", 19)
    # The second count in 0x525ba0 controls PAIRS of 76-byte records.
    reader.array("object0-pairs", (("words", 19), ("words", 19)))
    reader.placements("object1", 10)
    reader.array("music-names", (("text", 256),))
    reader.array("music-zones", (("words", 9),))
    reader.array("sound-names", (("text", 256),))
    for ordinal in range(reader.scalar("sound-zones", minimum=28)):
        reader.record("sound-zone-bounds", ordinal, (("words", 6),))
        reader.array(f"sound-zone-{ordinal}-members", (("words", 1),))
    reader.array("sound-spots", (("words", 5),))
    reader.array("unknown-regions", (("words", 7),))
    # These are the target reader's actual boundaries, including a 248-byte field.
    reader.array("portals", (("words", 7), ("text", 256), ("text", 248), ("words", 6)))
    for ordinal in range(reader.scalar("region-groups", minimum=4)):
        reader.array(f"region-group-{ordinal}", (("words", 9),))
    reader.array("named-areas", (("words", 7), ("text", 256), ("text", 256), ("words", 2)))
    # 0x528bcc subtracts point counts from the declared aggregate during iteration.
    aggregate = reader.scalar("npc-aggregate", minimum=12)
    used, ordinal, points = 0, 0, 0
    while used < aggregate:
        row = reader.record("npcs", ordinal, (("words", 6),))
        children = reader.array(f"npc-{ordinal}-points", (("words", 3),))
        row["point_count"] = len(children)
        used += 1 + len(children)
        points += len(children)
        ordinal += 1
    if used != aggregate:
        raise FormatError("NPC records/points exceed the declared aggregate")
    reader.counts.update({"npcs": ordinal, "npc-points": points})
    if signature == b"FLD\0":
        for name in ("sky-resource", "cloud0-resource", "cloud1-resource"):
            reader.record(name, fields=(("text", 256),))
    reader.record("trailer", fields=(("words", 11),))
    reader.finish()
    return {"signature_hex": signature.hex(), "variant": signature[:3].decode("ascii"),
            "extent_raw_i32": extent, "counts": reader.counts, "parts": reader.parts,
            "bytes_consumed": reader.position, "structured_round_trip_matches": True,
            "semantic_status": "unknown"}


def rebuild_wld(document, blob_root=None):
    """Reconstruct all bytes from structured exports, preserving opaque grid blocks."""
    output = bytearray()
    for part in document["parts"]:
        if part["offset"] != len(output):
            raise FormatError("WLD parts have a gap or overlap")
        if part["kind"] == "blob":
            raw = part.get("data")
            if raw is None:
                if blob_root is None:
                    raise FormatError("WLD reconstruction requires exported blob files")
                raw = target_path(blob_root, part["blob_path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != part["sha256"]:
                raise FormatError("WLD blob hash mismatch")
        elif part["kind"] in ("count", "scalar"):
            raw = struct.pack(part["layout"], part["value"])
        else:
            raw = bytearray()
            fields = sorted(part["numeric_blocks"] + part["texts"], key=lambda f: f["offset"])
            for field in fields:
                if field["offset"] != part["offset"] + len(raw):
                    raise FormatError("WLD record fields have a gap or overlap")
                raw.extend(bytes.fromhex(field["raw_hex"]) if "raw_hex" in field else
                           struct.pack(field["layout"], *field["values"]))
        if len(raw) != part["size_bytes"]:
            raise FormatError("WLD part extent differs from reconstructed bytes")
        output.extend(raw)
    if len(output) != document["bytes_consumed"]:
        raise FormatError("WLD reconstruction length mismatch")
    return bytes(output)


def bind_profile(executable, profile):
    if sha256_file(executable) != profile["executable_sha256"]:
        raise FormatError("Executable hash differs from the WLD evidence profile")
    with executable.open("rb") as stream:
        for window in profile["windows"]:
            stream.seek(int(window["file_offset"], 16))
            raw = stream.read(window["length"])
            if hashlib.sha256(raw).hexdigest() != window["source_bytes_sha256"]:
                raise FormatError(f"WLD loader evidence mismatch: {window['id']}")


def resource_targets(text, roots, paths):
    if text is None:
        return []
    name = text.replace("\\", "/")
    if not name or name.startswith("/") or any(p in (".", "..", "") for p in name.split("/")) or ":" in name:
        return []
    return sorted({entry for root in roots for entry in paths.get((root + "/" + name).casefold(), [])})


def run(args):
    profile = json.loads(args.profile.read_text())
    bind_profile(args.executable, profile)
    extraction = json.loads(args.extraction_report.read_text())
    manifest_hash = sha256_file(args.manifest)
    if manifest_hash != extraction["manifest"]["sha256"] or profile["baseline_id"] != extraction["baseline_id"]:
        raise FormatError("WLD inputs have inconsistent baseline/manifest identifiers")
    root, destination = args.extracted_root.resolve(), args.output_dir.resolve()
    for output in (destination, args.report.resolve()):
        for protected in (root, root.parent / "originals", root.parent / "decoded", args.executable.resolve().parent):
            if output == protected or protected in output.parents:
                raise FormatError("WLD outputs must be outside source directories")
    entries = [json.loads(line) for line in args.manifest.read_text().splitlines()]
    paths = defaultdict(list)
    for entry in entries:
        if entry["baseline_id"] != extraction["baseline_id"]:
            raise FormatError("Archive entry baseline differs from WLD evidence")
        paths[entry["original_path"].replace("\\", "/").casefold()].append(entry["id"])
    sources, totals, links, variants = [], Counter(), [], Counter()
    numeric_extremes = {}

    def export(name, rows):
        path = target_path(destination, name)
        data = b"".join((json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()
                        for row in rows)
        preserve_output(path, data)
        return {"path": str(path), "sha256": sha256_file(path), "rows": len(rows)}

    for entry in entries:
        if entry["extension"] != ".wld":
            continue
        source = {"id": entry["id"], "source_path": entry["original_path"],
                  "source_sha256": entry["content"]["sha256"], "size_bytes": entry["size_bytes"],
                  "status": "unknown", "semantic_status": "unknown"}
        try:
            path = target_path(root, entry["extracted_path"])
            data = path.read_bytes()
            if entry["content"]["status"] != "extracted" or len(data) != entry["size_bytes"] or hashlib.sha256(data).hexdigest() != source["source_sha256"]:
                raise FormatError("Extracted WLD size/hash mismatch")
            document = parse_wld(data)
            rows, local_links, names, index_counts = [], [], {}, Counter()
            for part in document["parts"]:
                if part["kind"] == "blob":
                    blob_name = f"blobs/{entry['id']}.{part['section']}.bin"
                    preserve_output(target_path(destination, blob_name), part.pop("data"))
                    part["blob_path"] = blob_name
                if part["kind"] != "record":
                    continue
                identifier = f"{entry['id']}:{part['section']}:{part['ordinal']:06d}"
                row = {"id": identifier, "archive_entry_id": entry["id"], "baseline_id": extraction["baseline_id"],
                       "source_sha256": source["source_sha256"], "domain": "maps", "schema_id": SCHEMA_ID,
                       "status": "decoded", "semantic_status": "unknown", "client_id": None, **part}
                group = part["section"].removesuffix("-names")
                if part["section"].endswith("-names"):
                    names.setdefault(group, []).append(identifier)
                roots = [part["resource_root"]] if "resource_root" in part else (
                    ["Sound/music", "Sound/back"] if group in ("music", "sound") else [])
                if roots:
                    text = part["texts"][0]
                    link = {"id": identifier + ":resource", "source_record_id": identifier,
                            "archive_entry_id": entry["id"], "baseline_id": extraction["baseline_id"],
                            "source_sha256": source["source_sha256"], "source_path": source["source_path"],
                            "domain": "maps", "schema_id": SCHEMA_ID, "offset": text["offset"],
                            "raw_value_hex": text["raw_hex"], "text": text["text"], "roots": roots,
                            "target_entry_ids": resource_targets(text["text"], roots, paths),
                            "status": "inferred", "basis": "Preserved filename matched within loader root or audio candidate roots"}
                    local_links.append(link)
                    row["resource_reference_id"] = link["id"]
                if part["section"].endswith("-placements"):
                    group = part["section"].removesuffix("-placements")
                    values = part["numeric_blocks"][0]["values"]
                    indices = values[1:2] if group == "mani" else values[:1]
                    group_names = names.get(group, [])
                    row["name_index_candidates"] = [{"value_raw_u32": i,
                                                       "record_field_offset": 4 if group == "mani" else 0,
                                                       "target_record_id": group_names[i] if i < len(group_names) else None,
                                                      "sentinel_candidate": i == 0xffffffff, "status": "inferred"}
                                                      for i in indices]
                    for candidate in row["name_index_candidates"]:
                        index_counts["sentinel" if candidate["sentinel_candidate"] else
                                     "matched" if candidate["target_record_id"] else "unresolved"] += 1
                for block_index, block in enumerate(part["numeric_blocks"]):
                    for field_index, value in enumerate(block["values"]):
                        key = f"{part['section']}:{block_index}:unknown_{field_index * 4:03d}_u32_bits"
                        minimum, maximum = numeric_extremes.get(key, (value, value))
                        numeric_extremes[key] = (min(minimum, value), max(maximum, value))
                rows.append(row)
            reconstructed = rebuild_wld(document, destination)
            if reconstructed != data:
                raise FormatError("Exported WLD reconstruction differs from source")
            reparsed = parse_wld(reconstructed)
            if reparsed["counts"] != document["counts"]:
                raise FormatError("WLD read/write/read counts differ")
            document.update({"archive_entry_id": entry["id"], "baseline_id": extraction["baseline_id"],
                             "source_path": source["source_path"], "source_sha256": source["source_sha256"],
                             "schema_id": SCHEMA_ID})
            raw_path = target_path(destination, entry["id"] + ".raw.json")
            preserve_output(raw_path, (json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
            saved = json.loads(raw_path.read_text())
            if rebuild_wld(saved, destination) != data:
                raise FormatError("Saved WLD export reconstruction differs from source")
            source.update({"status": "decoded", "variant": document["variant"], "extent_raw_i32": document["extent_raw_i32"],
                           "counts": document["counts"], "records": len(rows), "bytes_consumed": len(data),
                           "placement_name_index_candidates": dict(sorted(index_counts.items())),
                           "structured_round_trip_matches": True, "read_write_read_matches": True,
                           "raw_catalog": {"path": str(raw_path), "sha256": sha256_file(raw_path)},
                           "normalized_catalog": export(entry["id"] + ".jsonl", rows),
                           "first_record": {k: rows[0][k] for k in ("id", "section", "offset", "size_bytes")},
                           "last_record": {k: rows[-1][k] for k in ("id", "section", "offset", "size_bytes")}})
            totals.update(document["counts"])
            variants[document["variant"]] += 1
            links.extend(local_links)
        except (OSError, ValueError) as exc:
            source["error"] = str(exc)
        sources.append(source)
        if len(sources) % 10 == 0:
            print(f"WLD sources examined: {len(sources)}", flush=True)
    errors = [s for s in sources if s["status"] != "decoded"]
    report = {"id": SCHEMA_ID, "baseline_id": extraction["baseline_id"],
              "executable_sha256": profile["executable_sha256"], "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "tool": {"path": "tools/ep45-client/wld.py", "version": TOOL_VERSION, "sha256": sha256_file(Path(__file__))},
              "dependency_hashes": {name: sha256_file(Path(__file__).parent / name) for name in ("tables.py", "archive.py", "sdata.py")},
              "evidence_profile": {"id": profile["id"], "path": str(args.profile), "sha256": sha256_file(args.profile)},
              "archive_manifest_sha256": manifest_hash, "extraction_report_sha256": sha256_file(args.extraction_report),
              "sources_examined": len(sources), "sources_decoded": len(sources) - len(errors), "errors": errors,
              "variants": dict(sorted(variants.items())), "section_counts": dict(sorted(totals.items())),
              "cataloged_structural_records": sum(s.get("records", 0) for s in sources),
              "resource_references": export("resource-references.jsonl", links),
              "matched_resource_references": sum(bool(l["target_entry_ids"]) for l in links),
              "unresolved_resource_references": sum(not l["target_entry_ids"] for l in links),
              "placement_name_index_candidates": {
                  key: sum(s.get("placement_name_index_candidates", {}).get(key, 0) for s in sources)
                  for key in ("matched", "sentinel", "unresolved")},
              "numeric_extremes": {key: {"minimum_raw_u32": value[0], "maximum_raw_u32": value[1]}
                                   for key, value in sorted(numeric_extremes.items())},
              "fully_decoded_grid_payloads": 0, "fully_semantically_validated_formats": 0,
              "new_runtime_interactions": 0, "sources": sources}
    write_json(args.report, report)
    print(f"WLD structures decoded: {report['sources_decoded']}/{len(sources)}; errors={len(errors)}")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "extraction-report", "extracted-root", "executable", "profile", "output-dir", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
