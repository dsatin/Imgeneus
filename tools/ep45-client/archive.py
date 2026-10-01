#!/usr/bin/env python3
"""Inventory/extract a plain SAH/SAF archive without changing the client."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import struct
import sys
import tempfile

TOOL_VERSION = "2.0.0"
SEED_SIGNATURE = b"0001CBCEBC5B2784D3FC9A2A9DB84D1C3FEB6E99"
CHUNK_SIZE = 1024 * 1024


class FormatError(ValueError):
    pass


class Reader:
    def __init__(self, data, position=0):
        self.data = data
        self.position = position

    def take(self, size):
        if size < 0 or self.position + size > len(self.data):
            raise FormatError(f"Truncated SAH at byte {self.position}, requested {size}")
        result = self.data[self.position:self.position + size]
        self.position += size
        return result

    def number(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def count(self):
        value = self.number("<i")
        if value < 0 or value > len(self.data) // 4:
            raise FormatError(f"Invalid count {value} at {self.position - 4}")
        return value

    def name(self):
        size = self.count()
        raw = self.take(size)
        try:
            return raw.removesuffix(b"\0").decode("utf-8"), raw.hex()
        except UnicodeDecodeError as exc:
            raise FormatError(f"Invalid UTF-8 name at {self.position - size}") from exc


def normalized_path(original):
    path = original.replace("\\", "/")
    parts = path.split("/")
    if not path or path.startswith("/") or any(
        part in ("", ".", "..") or "\0" in part or ":" in part for part in parts
    ):
        raise FormatError(f"Unsafe archive path: {original!r}")
    return str(PurePosixPath(*parts))


def classify_path(path):
    root = path.split("/")[0].casefold()
    name = PurePosixPath(path).name.casefold()
    if name in ("skill.sdata", "npcskill.sdata"):
        return "skills"
    if name == "cash.sdata":
        return "economy"
    return {
        "character": "characters", "item": "items", "monster": "mobs",
        "npc": "npcs_quests", "world": "maps", "interface": "ui",
        "sound": "audio", "entity": "world_objects", "effect": "effects",
        "terrain": "maps", "sky": "maps", "strip": "world_objects",
        "cloak": "equipment_assets", "vehicle": "vehicle_assets",
        "cursor": "ui", "lensflare": "effects",
    }.get(root, "unclassified")


def read_entry(reader, folder, ordinal, kind):
    start = reader.position
    name, name_hex = reader.name()
    offset = reader.number("<q")
    size = reader.number("<i")
    version = reader.number("<i")
    original = f"{folder}/{name}" if folder else name
    errors = []
    try:
        path = normalized_path(original)
    except FormatError as exc:
        path = None
        errors.append(str(exc))
    return {
        "id": f"{kind}-{ordinal:06d}", "ordinal": ordinal,
        "entry_kind": kind, "original_path": original, "path": path,
        "name_bytes_hex": name_hex, "sah_record_offset": start,
        "sah_record_size_bytes": reader.position - start,
        "saf_offset": offset, "size_bytes": size, "version": version,
        "extension": PurePosixPath(path or name).suffix.casefold(),
        "domain_hint": classify_path(path) if path and kind == "tree" else "unclassified",
        "classification_basis": "path_hint", "errors": errors,
    }


def parse_sah(data):
    reader = Reader(data)
    if reader.take(3) != b"SAH":
        raise FormatError("Unsupported SAH signature; no encrypted-index fallback")
    version = reader.number("<i")
    declared_count = reader.count()
    padding = reader.take(40)
    entries, folders = [], []

    def folder(parent, depth=0):
        if depth > 128:
            raise FormatError("SAH tree exceeds supported depth")
        start = reader.position
        name, name_hex = reader.name()
        path = f"{parent}/{name}" if parent and name else parent or name
        file_count = reader.count()
        folders.append({"ordinal": len(folders), "original_path": path,
                        "name_bytes_hex": name_hex, "sah_offset": start,
                        "declared_files": file_count})
        for _ in range(file_count):
            entries.append(read_entry(reader, path, len(entries), "tree"))
        for _ in range(reader.count()):
            folder(path, depth + 1)

    folder("")
    tail_offset = reader.position
    tail = data[tail_offset:]
    supplemental = []
    tail_candidate_error = None
    # Some archives have file-shaped records after the complete tree.
    # Keep their structure and semantics separate from active tree entries.
    if tail:
        try:
            other = Reader(data, tail_offset)
            for ordinal in range(other.count()):
                supplemental.append(read_entry(other, "", ordinal, "supplemental"))
            if other.number("<i") != 0 or other.position != len(data):
                raise FormatError("Trailing block does not match count + file records + zero")
        except FormatError as exc:
            supplemental = []
            tail_candidate_error = str(exc)
    return {
        "signature": "SAH", "version": version, "declared_file_count": declared_count,
        "tree_file_count": len(entries), "folder_count": len(folders),
        "tree_bytes_consumed": tail_offset, "header_padding_hex": padding.hex(),
        "trailing": {"offset": tail_offset, "size_bytes": len(tail),
                     "sha256": hashlib.sha256(tail).hexdigest(),
                     "file_shaped_records": len(supplemental),
                     "semantics": "unknown", "candidate_error": tail_candidate_error},
        "entries": entries, "supplemental": supplemental, "folders": folders,
    }


def validate_index(index, saf_size):
    issues = []
    if index["declared_file_count"] != index["tree_file_count"]:
        issues.append({"kind": "count_mismatch", "declared": index["declared_file_count"],
                       "observed": index["tree_file_count"]})
    exact, folded = defaultdict(list), defaultdict(list)
    tree_paths = {e["path"] for e in index["entries"] if e["path"]}
    for entry in index["entries"] + index["supplemental"]:
        if entry["saf_offset"] < 0 or entry["size_bytes"] < 0 or entry["saf_offset"] + entry["size_bytes"] > saf_size:
            entry["errors"].append("Range outside SAF")
        if entry["entry_kind"] == "tree" and entry["path"]:
            exact[entry["path"]].append(entry["id"])
            folded[entry["path"].casefold()].append(entry["id"])
            if any(str(p) in tree_paths for p in PurePosixPath(entry["path"]).parents if str(p) != "."):
                entry["errors"].append("Archive file path is also used as a parent directory")
    duplicates = [{"path": p, "ids": ids} for p, ids in exact.items() if len(ids) > 1]
    case_collisions = [{"casefold_path": p, "ids": ids} for p, ids in folded.items() if len(ids) > 1]
    used = set()
    for entry in index["entries"] + index["supplemental"]:
        path = entry["path"]
        if not path or entry["errors"]:
            entry["extracted_path"] = None
        elif entry["entry_kind"] == "supplemental":
            entry["extracted_path"] = f"supplemental/{entry['ordinal']:06d}/{path}"
        elif path in used:
            entry["extracted_path"] = f"duplicates/{entry['ordinal']:06d}/{path}"
        else:
            entry["extracted_path"] = f"tree/{path}"
        used.add(path)
    # Track all overlaps, including nested/identical intervals, without assuming
    # an overlap means corruption: archives may share the same content range.
    overlaps, active = [], []
    valid = [e for e in index["entries"] if not e["errors"] and e["size_bytes"]]
    for entry in sorted(valid, key=lambda e: (e["saf_offset"], e["ordinal"])):
        active = [previous for previous in active if previous["saf_offset"] + previous["size_bytes"] > entry["saf_offset"]]
        for previous in active:
            overlaps.append({"ids": [previous["id"], entry["id"]],
                             "start": entry["saf_offset"],
                             "end": min(previous["saf_offset"] + previous["size_bytes"], entry["saf_offset"] + entry["size_bytes"])})
        active.append(entry)
    return {"issues": issues, "duplicates": duplicates,
            "case_collisions": case_collisions, "tree_overlaps": overlaps,
            "invalid_entries": [e["id"] for e in index["entries"] + index["supplemental"] if e["errors"]]}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def content_hint(header, extension):
    if header.startswith(SEED_SIGNATURE):
        return "seed_sdata_header"
    for signature, kind in [(b"DDS ", "dds"), (b"BM", "bmp"), (b"\x89PNG\r\n\x1a\n", "png"),
                            (b"\xff\xd8\xff", "jpeg"), (b"PK\x03\x04", "zip"), (b"MZ", "pe_candidate"),
                            (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "compound_file_header")]:
        if header.startswith(signature):
            return kind
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "wave"
    return f"extension_only:{extension}" if extension else "unknown"


def target_path(root, relative):
    normalized_path(relative)
    target = root / relative
    # Refuse symlinks even if their resolved target is still inside the cache.
    for part in [target, *target.parents]:
        if part.is_symlink():
            raise FormatError(f"Symlink in extraction path: {relative}")
        if part == root:
            break
    if root not in target.resolve().parents:
        raise FormatError(f"Extraction escaped cache: {relative}")
    return target


def process_entry(stream, entry, output_root, extract):
    stream.seek(entry["saf_offset"])
    digest = hashlib.sha256()
    header = bytearray()
    target = temporary = None
    writer = None
    try:
        if extract:
            target = target_path(output_root, entry["extracted_path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                fd, temp_name = tempfile.mkstemp(prefix=".extract-", dir=target.parent)
                temporary = Path(temp_name)
                writer = os.fdopen(fd, "wb")
        remaining = entry["size_bytes"]
        while remaining:
            block = stream.read(min(CHUNK_SIZE, remaining))
            if not block:
                raise FormatError("Truncated SAF range")
            remaining -= len(block)
            digest.update(block)
            if len(header) < 64:
                header.extend(block[:64 - len(header)])
            if writer:
                writer.write(block)
        if writer:
            writer.close()
            writer = None
            os.link(temporary, target)  # Never replace an existing raw file.
        content_hash = digest.hexdigest()
        if extract and sha256_file(target) != content_hash:
            raise FormatError("Existing/extracted file hash differs from its source SAF range")
        return {"status": "extracted" if extract else "inventoried",
                "sha256": content_hash, "prefix_hex": bytes(header).hex(),
                "format_hint": content_hint(bytes(header), entry["extension"]),
                "verification": "source_range_matches_extracted_file" if extract else "source_range_hashed"}
    finally:
        if writer:
            writer.close()
        if temporary:
            temporary.unlink(missing_ok=True)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(client_dir, output_dir, report_dir, baseline_id, extract=False, expected_manifest=None):
    for destination in (output_dir, report_dir):
        if destination == client_dir or client_dir in destination.parents:
            raise FormatError("Output/report directory must be outside the client")
    sah, saf = client_dir / "data.sah", client_dir / "data.saf"
    before = [(p.stat().st_size, p.stat().st_mtime_ns) for p in (sah, saf)]
    sources = {"data.sah": sha256_file(sah), "data.saf": sha256_file(saf)}
    if expected_manifest:
        expected = {e["path"]: e["sha256"] for e in json.loads(expected_manifest.read_text())["files"]}
        if any(expected.get(name) != digest for name, digest in sources.items()):
            raise FormatError("Archive hashes do not match the selected baseline")
    index = parse_sah(sah.read_bytes())
    checks = validate_index(index, saf.stat().st_size)
    entries = index.pop("entries") + index.pop("supplemental")
    folders = index.pop("folders")
    print(f"Indexed {index['tree_file_count']} tree files, {len(folders)} folders, {index['trailing']['file_shaped_records']} supplemental records", flush=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "archive-files.jsonl"
    temporary_manifest = output_dir / "archive-files.jsonl.pending"
    counts, formats = Counter(), Counter()
    failures = []
    with saf.open("rb") as stream, temporary_manifest.open("w", encoding="utf-8") as manifest:
        for i, entry in enumerate(entries):
            entry["baseline_id"] = baseline_id
            if entry["errors"] or checks["issues"]:
                result = {"status": "unknown", "error": entry["errors"] or checks["issues"]}
            else:
                try:
                    result = process_entry(stream, entry, output_dir / "extracted", extract)
                except (OSError, ValueError) as exc:
                    result = {"status": "unknown", "error": str(exc)}
            entry["content"] = result
            counts[f"{entry['entry_kind']}:{result['status']}"] += 1
            formats[result.get("format_hint", "unreadable")] += 1
            if "error" in result:
                failures.append({"id": entry["id"], "path": entry["original_path"], "error": result["error"]})
            manifest.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
            if (i + 1) % 2000 == 0:
                print(f"Processed {i + 1}/{len(entries)}; errors={len(failures)}", flush=True)
    after = [(p.stat().st_size, p.stat().st_mtime_ns) for p in (sah, saf)]
    if before != after or sources != {"data.sah": sha256_file(sah), "data.saf": sha256_file(saf)}:
        raise FormatError("Source archive changed during processing; pending manifest is not valid")
    temporary_manifest.replace(manifest_path)
    write_json(output_dir / "archive-folders.json", folders)
    report = {
        "schema_version": 2, "baseline_id": baseline_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool": {"path": "tools/ep45-client/archive.py", "version": TOOL_VERSION,
                 "python": platform.python_version(), "sha256": sha256_file(Path(__file__))},
        "mode": "extract" if extract else "inventory", "sources": sources,
        "saf_size_bytes": saf.stat().st_size, "index": index,
        "manifest": {"path": str(manifest_path), "sha256": sha256_file(manifest_path),
                     "size_bytes": manifest_path.stat().st_size, "records": len(entries)},
        "counts": dict(sorted(counts.items())), "content_hints": dict(sorted(formats.items())),
        "by_extension": dict(sorted(Counter(e["extension"] for e in entries if e["entry_kind"] == "tree").items())),
        "by_domain_hint": dict(sorted(Counter(e["domain_hint"] for e in entries if e["entry_kind"] == "tree").items())),
        "by_root": dict(sorted(Counter(e["path"].split("/")[0] for e in entries if e["entry_kind"] == "tree" and e["path"]).items())),
        "tree_content_bytes": sum(e["size_bytes"] for e in entries if e["entry_kind"] == "tree"),
        "validation": checks, "errors": failures,
        "semantics_decoded": False,
    }
    write_json(report_dir / "extraction-report.json", report)
    print(f"Finished: {dict(counts)}; {len(failures)} errors; manifest={manifest_path}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inventory", "extract"))
    parser.add_argument("--client-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--baseline-id", required=True)
    parser.add_argument("--expected-manifest", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.client_dir.resolve(), args.output_dir.resolve(),
                     args.report_dir.resolve(), args.baseline_id, args.mode == "extract", args.expected_manifest)
        return 1 if report["errors"] or report["validation"]["issues"] else 0
    except (OSError, ValueError) as exc:
        print(f"Archive error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
