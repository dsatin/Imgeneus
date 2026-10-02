#!/usr/bin/env python3
"""Decode client dungeon/water structures and audit their map/resource dependencies."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from archive import FormatError, sha256_file, target_path, write_json
from sdata import preserve_output
from wld import WldReader, bind_profile, resource_targets

TOOL_VERSION = "1.0.0"
SCHEMA_ID = "EP45-A3-SPATIAL-001"


class SpatialReader(WldReader):
    def scalar(self, section, kind="i", minimum=None, **metadata):
        value = super().scalar(section, kind, minimum)
        self.parts[-1].update(metadata)
        return value

    def mesh_array(self, section, count, layout, **metadata):
        offset, width = self.position, struct.calcsize(layout)
        raw = self.take(count * width)
        values = [list(row) for row in struct.iter_unpack(layout, raw)]
        for row in values:
            self.rebuilt.extend(struct.pack(layout, *row))
        part = {"section": section, "kind": "array", "offset": offset,
                "size_bytes": len(raw), "count": count, "layout": layout,
                "values": values, **metadata}
        self.parts.append(part)
        self.counts[section] = self.counts.get(section, 0) + count
        return part

    def indices(self, section, count, vertices, **metadata):
        part = self.mesh_array(section, count, "<HHH", **metadata)
        if any(index >= vertices for row in part["values"] for index in row):
            raise FormatError(f"Mesh index exceeds vertex count at {part['offset']}")
        return part


def parse_water(data):
    reader = SpatialReader(data)
    reader.record("water-header", fields=(("words", 3),))
    reader.array("texture-names", (("text", 256),))
    reader.finish()
    return {"variant": "WTR", "counts": reader.counts, "parts": reader.parts,
            "bytes_consumed": reader.position, "structured_round_trip_matches": True,
            "semantic_status": "unknown"}


def parse_dungeon(data):
    reader = SpatialReader(data)
    reader.record("dungeon-header", fields=(("words", 6),))
    reader.array("texture-names", (("text", 256),))
    pages = reader.scalar("external-page-count")
    if pages < 0:
        raise FormatError("Negative external page count")
    reader.counts["external-page-count"] = pages
    flag = reader.scalar("root-present", "I")
    totals = Counter()
    max_depth = 0

    def node(node_path="root", parent_path=None, child_slot=None, depth=0):
        nonlocal max_depth
        # This is a tool resource bound, not a recovered gameplay/client limit.
        if depth > 64:
            raise FormatError("Dungeon tree exceeds the tool's depth bound of 64")
        max_depth = max(max_depth, depth)
        totals["nodes"] += 1
        context = {"node_path": node_path}
        reader.record("node-header", fields=(("words", 15),), **context,
                      parent_node_path=parent_path, child_slot=child_slot, depth=depth)
        groups = reader.scalar("node-group-count", minimum=8, **context)
        totals["groups"] += groups
        for group in range(groups):
            group_context = {**context, "group_ordinal": group}
            reader.record("group-header", group, (("words", 1),), **group_context)
            patches = reader.scalar("group-patch-count", minimum=8, **group_context)
            totals["patches"] += patches
            for patch in range(patches):
                patch_context = {**group_context, "patch_ordinal": patch}
                reader.record("patch-header", patch, (("words", 1),), **patch_context)
                vertices = reader.scalar("patch-vertex-count", minimum=44, **patch_context)
                if vertices:
                    reader.mesh_array("render-vertices", vertices, "<" + "I" * 11, **patch_context)
                    faces = reader.scalar("patch-triangle-count", minimum=6, **patch_context)
                    reader.indices("render-triangles", faces, vertices, **patch_context)
                # The target reader skips the triangle count when vertices == 0.
        present = reader.scalar("auxiliary-mesh-present", "I", **context)
        if present:
            totals["auxiliary-meshes"] += 1
            vertices = reader.scalar("auxiliary-vertex-count", minimum=12, **context)
            reader.mesh_array("auxiliary-vertices", vertices, "<III", **context)
            faces = reader.scalar("auxiliary-triangle-count", minimum=6, **context)
            reader.indices("auxiliary-triangles", faces, vertices, **context)
        for slot in range(8):
            present = reader.scalar("child-present", "I", **context, child_slot=slot)
            if present:
                node(f"{node_path}/{slot}", node_path, slot, depth + 1)

    if flag:
        node()
    reader.finish()
    # Per-node count fields repeat; totals, rather than the last scalar, are authoritative.
    counts = {key: reader.counts.get(key, 0) for key in
              ("texture-names", "external-page-count", "render-vertices", "render-triangles",
               "auxiliary-vertices", "auxiliary-triangles")}
    counts.update({key: totals[key] for key in ("nodes", "groups", "patches", "auxiliary-meshes")})
    counts["max-depth"] = max_depth
    return {"variant": "DG", "counts": counts, "parts": reader.parts,
            "bytes_consumed": reader.position, "structured_round_trip_matches": True,
            "semantic_status": "unknown"}


def rebuild_spatial(document):
    output = bytearray()
    for part in document["parts"]:
        if part["offset"] != len(output):
            raise FormatError("Spatial parts have a gap or overlap")
        raw = bytearray()
        if part["kind"] == "array":
            if len(part["values"]) != part["count"]:
                raise FormatError("Spatial array count differs from structured rows")
            for row in part["values"]:
                raw.extend(struct.pack(part["layout"], *row))
        elif part["kind"] in ("count", "scalar"):
            raw.extend(struct.pack(part["layout"], part["value"]))
        elif part["kind"] == "record":
            for field in sorted(part["numeric_blocks"] + part["texts"], key=lambda f: f["offset"]):
                if field["offset"] != part["offset"] + len(raw):
                    raise FormatError("Spatial fields have a gap or overlap")
                raw.extend(bytes.fromhex(field["raw_hex"]) if "raw_hex" in field else
                           struct.pack(field["layout"], *field["values"]))
        else:
            raise FormatError("Unknown spatial part kind")
        if len(raw) != part["size_bytes"]:
            raise FormatError("Spatial part extent differs from reconstructed bytes")
        output.extend(raw)
    if len(output) != document["bytes_consumed"]:
        raise FormatError("Spatial reconstruction length mismatch")
    return bytes(output)


def resource_link(entry, text, roots, paths, section, ordinal=0, **metadata):
    name = text["text"]
    exact = resource_targets(name, roots, paths)
    alternate = []
    if name and not exact and "." in name:
        # Same-stem DDS matches are candidates only: no replacement behavior is proven.
        alternate = resource_targets(name.rsplit(".", 1)[0] + ".dds", roots, paths)
    return {"id": f"{entry['id']}:{section}:{ordinal:06d}:resource",
            "archive_entry_id": entry["id"], "source_path": entry["original_path"],
            "source_sha256": entry["content"]["sha256"], "baseline_id": entry["baseline_id"],
            "domain": "maps", "schema_id": SCHEMA_ID, "offset": text["offset"],
            "size_bytes": text["size_bytes"], "raw_value_hex": text["raw_hex"], "text": name,
            "roots": roots, "target_entry_ids": exact,
            "same_stem_dds_candidate_entry_ids": alternate,
            "status": "inferred", "runtime_status": "unknown",
            "basis": "Exact filename within the client loader root; alternate DDS matches remain hypotheses",
            **metadata}


def export_json(path, document):
    preserve_output(path, (json.dumps(document, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode())
    return {"path": str(path), "sha256": sha256_file(path)}


def export_rows(path, rows):
    preserve_output(path, b"".join((json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()
                                 for row in rows))
    return {"path": str(path), "sha256": sha256_file(path), "rows": len(rows)}


def validate_outputs(outputs, sources):
    sources = tuple(sources)
    for output in outputs:
        output = output.resolve()
        for source in sources:
            source = source.resolve()
            if output == source or source in output.parents:
                raise FormatError("Spatial outputs must be outside source/reference directories")


def run(args):
    profile = json.loads(args.profile.read_text())
    bind_profile(args.executable, profile)
    with args.executable.open("rb") as stream:
        for field in profile["strings"]:
            stream.seek(int(field["file_offset"], 16))
            raw = stream.read(field["length"])
            if raw.hex() != field["raw_hex"] or hashlib.sha256(raw).hexdigest() != field["source_bytes_sha256"]:
                raise FormatError("Spatial evidence string differs from executable bytes")
    extraction = json.loads(args.extraction_report.read_text())
    manifest_hash = sha256_file(args.manifest)
    if manifest_hash != extraction["manifest"]["sha256"] or profile["baseline_id"] != extraction["baseline_id"]:
        raise FormatError("Spatial inputs have inconsistent baseline/manifest identifiers")
    wld_index = json.loads(args.wld_index.read_text())
    if (wld_index["baseline_id"] != extraction["baseline_id"] or
            wld_index["archive_manifest_sha256"] != manifest_hash or
            wld_index["executable_sha256"] != profile["executable_sha256"]):
        raise FormatError("WLD reference index differs from the spatial baseline")
    root, destination = args.extracted_root.resolve(), args.output_dir.resolve()
    validate_outputs((destination, args.report), (root, root.parent / "originals", root.parent / "decoded",
                     args.executable.resolve().parent, args.manifest, args.extraction_report, args.profile, args.wld_index))
    entries = [json.loads(line) for line in args.manifest.read_text().splitlines()]
    paths, by_id = defaultdict(list), {}
    for entry in entries:
        if entry["baseline_id"] != extraction["baseline_id"] or entry["id"] in by_id:
            raise FormatError("Archive baseline/entry identifiers are inconsistent")
        paths[entry["original_path"].replace("\\", "/").casefold()].append(entry["id"])
        by_id[entry["id"]] = entry
    validate_outputs((destination, args.report), (Path(s["raw_catalog"]["path"]).parent for s in wld_index["sources"] if "raw_catalog" in s))
    sources, totals, variants, links, group_indices, extrema = [], Counter(), Counter(), [], Counter(), {}
    mesh_extrema = {}
    for entry in entries:
        if entry["extension"] not in (".dg", ".wtr", ".dg_pv"):
            continue
        source = {"id": entry["id"], "source_path": entry["original_path"], "extension": entry["extension"],
                  "source_sha256": entry["content"]["sha256"], "size_bytes": entry["size_bytes"],
                  "status": "unknown", "semantic_status": "unknown"}
        try:
            data = target_path(root, entry["extracted_path"]).read_bytes()
            if entry["content"]["status"] != "extracted" or len(data) != entry["size_bytes"] or hashlib.sha256(data).hexdigest() != source["source_sha256"]:
                raise FormatError("Extracted spatial-resource size/hash mismatch")
            source["source_integrity_verified"] = True
            document = parse_water(data) if entry["extension"] == ".wtr" else parse_dungeon(data)
            if entry["extension"] == ".dg_pv":
                raise FormatError("DG_PV candidate needs its own verified client loader; DG compatibility is unproven")
            source_links, rows = [], []
            textures = document["counts"]["texture-names"]
            for ordinal, part in enumerate(document["parts"]):
                identifier = f"{entry['id']}:part:{ordinal:06d}"
                row = {"id": identifier, "archive_entry_id": entry["id"], "baseline_id": entry["baseline_id"],
                       "source_sha256": source["source_sha256"], "source_path": source["source_path"],
                       "domain": "maps", "schema_id": SCHEMA_ID, "status": "decoded",
                       "semantic_status": "unknown", "client_id": None, **part}
                if part["section"] == "texture-names" and part["kind"] == "record":
                    roots = ["Entity/Water"] if document["variant"] == "WTR" else ["Entity/Texture"]
                    link = resource_link(entry, part["texts"][0], roots, paths, "texture-names", part["ordinal"])
                    source_links.append(link)
                    row["resource_reference_id"] = link["id"]
                if part["section"] == "group-header":
                    value = part["numeric_blocks"][0]["values"][0]
                    matched = value < textures
                    row["texture_index_candidate"] = {"value_raw_u32": value, "status": "inferred",
                        "target_reference_id": f"{entry['id']}:texture-names:{value:06d}:resource" if matched else None}
                    group_indices["matched" if matched else "unresolved"] += 1
                for block in part.get("numeric_blocks", []):
                    for i, value in enumerate(block["values"]):
                        key = f"{part['section']}:unknown_{i * 4:03d}_u32_bits"
                        low, high = extrema.get(key, (value, value))
                        extrema[key] = (min(low, value), max(high, value))
                if part["kind"] == "array":
                    width = 2 if part["layout"] == "<HHH" else 4
                    for i, column in enumerate(zip(*part["values"])):
                        key = f"{part['section']}:unknown_{i * width:03d}_u{width * 8}_bits"
                        low, high = min(column), max(column)
                        previous = mesh_extrema.get(key, (low, high))
                        mesh_extrema[key] = (min(previous[0], low), max(previous[1], high))
                rows.append(row)
            if document["variant"] == "DG":
                stem = Path(entry["original_path"]).stem
                # The count controls external DDS requests; it consumes no extra DG bytes.
                pages = document["counts"]["external-page-count"]
                if pages > len(entries):
                    raise FormatError("External page expansion exceeds the manifest-size tool bound")
                count_part = next(p for p in document["parts"] if p["section"] == "external-page-count")
                for i in range(pages):
                    text = {"text": f"{stem}/{stem}_L{i}.dds", "offset": count_part["offset"],
                            "size_bytes": 4, "raw_hex": struct.pack("<i", pages).hex()}
                    source_links.append(resource_link(entry, text, ["world/dungeon"], paths, "external-pages", i,
                        basis="Filename generated by 0x591f60 using %s\\%s_L%d.%s; source span holds the page count"))
            if rebuild_spatial(document) != data:
                raise FormatError("Spatial structured reconstruction differs from source")
            document.update({"archive_entry_id": entry["id"], "baseline_id": entry["baseline_id"],
                             "source_path": source["source_path"], "source_sha256": source["source_sha256"], "schema_id": SCHEMA_ID})
            raw_path = target_path(destination, entry["id"] + ".raw.json")
            raw_index = export_json(raw_path, document)
            saved = json.loads(raw_path.read_text())
            rebuilt = rebuild_spatial(saved)
            if rebuilt != data or (parse_water(rebuilt) if document["variant"] == "WTR" else parse_dungeon(rebuilt))["counts"] != document["counts"]:
                raise FormatError("Saved spatial read/write/read validation failed")
            source.update({"status": "decoded", "variant": document["variant"], "counts": document["counts"],
                           "catalog_rows": len(rows), "bytes_consumed": len(data), "raw_catalog": raw_index,
                           "normalized_catalog": export_rows(target_path(destination, entry["id"] + ".jsonl"), rows),
                           "structured_round_trip_matches": True, "read_write_read_matches": True,
                           "first_part": {k: rows[0][k] for k in ("id", "section", "offset", "size_bytes")},
                           "last_part": {k: rows[-1][k] for k in ("id", "section", "offset", "size_bytes")}})
            totals.update({k: v for k, v in document["counts"].items() if k != "max-depth"})
            variants[document["variant"]] += 1
            links.extend(source_links)
        except (OSError, ValueError, struct.error) as exc:
            source["error"] = str(exc)
        sources.append(source)
        if len(sources) % 10 == 0:
            print(f"Spatial sources examined: {len(sources)}", flush=True)
    map_links = []
    for source in wld_index["sources"]:
        entry = by_id[source["id"]]
        if source["source_sha256"] != entry["content"]["sha256"]:
            raise FormatError("WLD source differs from the archive manifest")
        if source["status"] != "decoded":
            continue
        path = Path(source["raw_catalog"]["path"])
        if sha256_file(path) != source["raw_catalog"]["sha256"]:
            raise FormatError("WLD raw catalog hash mismatch")
        document = json.loads(path.read_text())
        for part in document["parts"]:
            if part["section"] == "inner-resource":
                roots = ["world/dungeon"] if source["variant"] == "DUN" else ["Entity/Water"]
                map_links.append(resource_link(entry, part["texts"][0], roots, paths, "inner-resource"))
    errors = [s for s in sources if s["status"] != "decoded"]
    all_links = links + map_links
    report = {"id": SCHEMA_ID, "baseline_id": extraction["baseline_id"],
              "executable_sha256": profile["executable_sha256"], "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "project_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "reproduction_arguments": ["python3", "tools/ep45-client/spatial.py"] +
                  [value for name in ("manifest", "extraction-report", "extracted-root", "executable", "profile", "wld-index", "output-dir", "report")
                   for value in ("--" + name, str(getattr(args, name.replace("-", "_"))))],
              "tool": {"path": "tools/ep45-client/spatial.py", "version": TOOL_VERSION, "sha256": sha256_file(Path(__file__))},
              "dependency_hashes": {name: sha256_file(Path(__file__).parent / name) for name in ("wld.py", "tables.py", "archive.py", "sdata.py")},
              "evidence_profile": {"id": profile["id"], "path": str(args.profile), "sha256": sha256_file(args.profile)},
              "archive_manifest_sha256": manifest_hash, "extraction_report_sha256": sha256_file(args.extraction_report),
              "wld_catalog_index_sha256": sha256_file(args.wld_index),
              "sources_examined": len(sources), "sources_decoded": len(sources) - len(errors), "errors": errors,
              "sources_by_extension": dict(sorted(Counter(s["extension"] for s in sources).items())),
              "decoded_structure_families": len(variants), "variants": dict(sorted(variants.items())),
              "section_counts": dict(sorted(totals.items())),
              "cataloged_structural_rows": sum(s.get("catalog_rows", 0) for s in sources),
              "source_bytes_verified": sum(s["size_bytes"] for s in sources if s.get("source_integrity_verified")),
              "source_bytes_structurally_decoded": sum(s.get("bytes_consumed", 0) for s in sources),
              "resource_references": export_rows(target_path(destination, "resource-references.jsonl"), all_links),
              "map_resource_references": len(map_links),
              "exact_matched_resource_references": sum(bool(l["target_entry_ids"]) for l in all_links),
              "unresolved_resource_references": sum(not l["target_entry_ids"] for l in all_links),
              "same_stem_dds_candidate_references": sum(bool(l["same_stem_dds_candidate_entry_ids"]) for l in all_links),
              "empty_resource_references": sum(l["text"] == "" for l in all_links),
              "group_texture_index_candidates": dict(sorted(group_indices.items())),
              "numeric_extremes": {key: {"minimum_raw_u32": value[0], "maximum_raw_u32": value[1]} for key, value in sorted(extrema.items())},
              "mesh_cell_extremes": {key: {"minimum_raw_bits": value[0], "maximum_raw_bits": value[1]} for key, value in sorted(mesh_extrema.items())},
              "maximum_observed_tree_depth": max((s.get("counts", {}).get("max-depth", 0) for s in sources), default=0),
              "fully_semantically_validated_formats": 0, "new_runtime_interactions": 0, "sources": sources}
    write_json(args.report, report)
    print(f"Spatial structures decoded: {report['sources_decoded']}/{len(sources)}; unresolved sources={len(errors)}")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "extraction-report", "extracted-root", "executable", "profile", "wld-index", "output-dir", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
