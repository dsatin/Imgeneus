"""Verify spatial source fixtures, tree boundaries, mesh indices, and output safety."""

import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

from archive import FormatError
from spatial import (SpatialReader, export_json, export_rows, parse_dungeon, parse_water,
                     rebuild_spatial, resource_link, validate_outputs)
from spatial import run
from spatial_loaders import file_offset


def envelope(node=None, flag=1):
    return bytes(32) + struct.pack("<I", flag if node is not None else 0) + (node or b"")


def leaf(groups=b"", group_count=0, auxiliary=b""):
    return (bytes(60) + struct.pack("<i", group_count) + groups +
            struct.pack("<I", bool(auxiliary)) + auxiliary + bytes(32))


def patch(vertices, indices, vertex_count=1, flag=0):
    data = struct.pack("<Ii", flag, vertex_count)
    if vertex_count:
        data += vertices + struct.pack("<i", len(indices)) + b"".join(struct.pack("<HHH", *r) for r in indices)
    return data


class SpatialTests(unittest.TestCase):
    def test_extracted_water_and_leaf_fixtures_round_trip(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/spatial-samples.json").read_text())
        for sample in fixture["samples"]:
            with self.subTest(source=sample["id"]):
                raw = bytes.fromhex(sample["raw_hex"])
                self.assertEqual(len(raw), sample["size_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), sample["span_sha256"])
                data = bytes.fromhex(sample.get("synthetic_envelope_hex", "")) + raw
                doc = parse_water(data) if sample["kind"] == "complete-water-file" else parse_dungeon(data)
                self.assertEqual(doc["counts"], sample["expected_counts"])
                self.assertEqual(rebuild_spatial(json.loads(json.dumps(doc))), data)

    def test_all_truncated_minimal_dungeon_and_water_prefixes(self):
        for data, parser in ((envelope(leaf()), parse_dungeon), (bytes(16), parse_water)):
            for size in range(len(data)):
                with self.subTest(size=size, parser=parser.__name__), self.assertRaises(FormatError):
                    parser(data[:size])
            with self.assertRaises(FormatError):
                parser(data + b"x")

    def test_invalid_counts_at_each_nested_boundary(self):
        valid = envelope(leaf(struct.pack("<ii", 0, 1) + patch(bytes(44), [(0, 0, 0)]), 1,
                              struct.pack("<i3Ii3H", 1, 0, 0, 0, 1, 0, 0, 0)))
        doc = parse_dungeon(valid)
        for part in doc["parts"]:
            if part["kind"] != "count" and part["section"] != "external-page-count":
                continue
            for value in ((-1,) if part["section"] == "external-page-count" else (-1, 0x7fffffff)):
                corrupted = bytearray(valid)
                struct.pack_into("<i", corrupted, part["offset"], value)
                with self.subTest(section=part["section"], value=value), self.assertRaises(FormatError):
                    parse_dungeon(bytes(corrupted))
        for count in (-1, 0x7fffffff):
            with self.assertRaises(FormatError):
                parse_water(bytes(12) + struct.pack("<i", count))

    def test_empty_root_and_external_pages_do_not_consume_geometry(self):
        raw = bytes(28) + struct.pack("<iI", 7, 0)
        doc = parse_dungeon(raw)
        self.assertEqual(doc["counts"]["external-page-count"], 7)
        self.assertEqual(doc["counts"]["nodes"], 0)
        self.assertEqual(rebuild_spatial(doc), raw)

    def test_zero_vertex_patch_has_no_triangle_count(self):
        group = struct.pack("<ii", 0, 2) + patch(b"", [], 0) + patch(bytes(44), [])
        doc = parse_dungeon(envelope(leaf(group, 1)))
        self.assertEqual(doc["counts"]["patches"], 2)
        self.assertEqual(doc["counts"]["render-vertices"], 1)
        self.assertEqual(len([p for p in doc["parts"] if p["section"] == "patch-triangle-count"]), 1)

    def test_raw_float_bits_and_nonzero_flags_are_preserved(self):
        values = [0x7fc0abcd, 0x80000000, 0x7f800001] + [0] * 8
        group = struct.pack("<ii", -1, 1) + patch(struct.pack("<11I", *values), [(0, 0, 0)], flag=0xffffffff)
        raw = envelope(leaf(group, 1), flag=0xffffffff)
        doc = parse_dungeon(raw)
        vertices = next(p for p in doc["parts"] if p["section"] == "render-vertices")
        self.assertEqual(vertices["values"], [values])
        self.assertEqual(rebuild_spatial(doc), raw)

    def test_render_and_auxiliary_indices_reject_out_of_range(self):
        with self.assertRaises(FormatError):
            parse_dungeon(envelope(leaf(struct.pack("<ii", 0, 1) + patch(bytes(44), [(0, 1, 0)]), 1)))
        auxiliary = struct.pack("<i3Ii3H", 1, 0, 0, 0, 1, 0, 0, 1)
        with self.assertRaises(FormatError):
            parse_dungeon(envelope(leaf(auxiliary=auxiliary)))
        reader = SpatialReader(struct.pack("<3H", 0, 65534, 65535))
        self.assertEqual(reader.indices("fixture", 1, 65536)["values"], [[0, 65534, 65535]])

    def test_eight_child_slots_retain_parent_path_and_nonzero_presence(self):
        root = bytes(68) + struct.pack("<I", 2) + leaf() + bytes(28)
        doc = parse_dungeon(envelope(root))
        headers = [p for p in doc["parts"] if p["section"] == "node-header"]
        self.assertEqual([p["node_path"] for p in headers], ["root", "root/0"])
        self.assertEqual(headers[1]["parent_node_path"], "root")
        self.assertEqual(headers[1]["child_slot"], 0)
        self.assertEqual(doc["counts"]["nodes"], 2)
        with self.assertRaises(FormatError):
            parse_dungeon(envelope(root[:-4]))

    def test_tree_depth_bound_is_explicit(self):
        node = leaf()
        for _ in range(65):
            node = bytes(68) + struct.pack("<I", 1) + node + bytes(28)
        with self.assertRaisesRegex(FormatError, "tool's depth bound"):
            parse_dungeon(envelope(node))

    def test_water_text_padding_unknown_encoding_and_count(self):
        text = b"\xff\0" + b"p" * 254
        raw = bytes(12) + struct.pack("<i", 1) + text
        doc = parse_water(raw)
        record = doc["parts"][-1]["texts"][0]
        self.assertIsNone(record["text"])
        self.assertEqual(record["padding_nonzero_bytes"], 254)
        self.assertEqual(rebuild_spatial(doc), raw)

    def test_reconstruction_rejects_gaps_lengths_and_array_corruption(self):
        raw = envelope(leaf(struct.pack("<ii", 0, 1) + patch(bytes(44), []), 1))
        doc = parse_dungeon(raw)
        for field in ("offset", "size_bytes"):
            changed = copy.deepcopy(doc)
            changed["parts"][0][field] += 1
            with self.assertRaises(FormatError):
                rebuild_spatial(changed)
        changed = copy.deepcopy(doc)
        next(p for p in changed["parts"] if p["kind"] == "array")["count"] += 1
        with self.assertRaises(FormatError):
            rebuild_spatial(changed)

    def test_resource_links_keep_exact_and_dds_candidates_separate(self):
        entry = {"id": "fixture", "original_path": "fixture.wtr", "content": {"sha256": "0" * 64}, "baseline_id": "fixture"}
        text = {"text": "A.tga", "offset": 16, "size_bytes": 256, "raw_hex": "00"}
        paths = {"entity/water/a.dds": ["second", "first"]}
        link = resource_link(entry, text, ["Entity/Water"], paths, "texture-names")
        self.assertEqual(link["target_entry_ids"], [])
        self.assertEqual(link["same_stem_dds_candidate_entry_ids"], ["first", "second"])
        paths["entity/water/a.tga"] = ["exact"]
        self.assertEqual(resource_link(entry, text, ["Entity/Water"], paths, "texture-names")["target_entry_ids"], ["exact"])
        text["text"] = "../A.tga"
        self.assertEqual(resource_link(entry, text, ["Entity/Water"], paths, "texture-names")["same_stem_dds_candidate_entry_ids"], [])

    def test_outputs_protect_all_sources_even_from_generators(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            validate_outputs((root / "out",), (root / "input",))
            with self.assertRaises(FormatError):
                validate_outputs((root / "out", root / "input/report.json"), (p for p in [root / "input"]))
            output = root / "out/data.json"
            first = export_json(output, {"value": 1})
            self.assertEqual(export_json(output, {"value": 1}), first)
            with self.assertRaises(FormatError):
                export_json(output, {"value": 2})
            self.assertEqual(export_rows(root / "rows.jsonl", [{"value": [1, 2]}])["rows"], 1)

    def test_pe_mapping_uses_section_offsets(self):
        pe = {"image_base": 0x400000, "sections": [{"rva": 0x1000, "file_offset": 0x400, "file_size": 0x200}]}
        self.assertEqual(file_offset(pe, 0x401020, 16), 0x420)
        with self.assertRaises(FormatError):
            file_offset(pe, 0x4011ff, 2)

    def test_cli_retains_failed_sources_verifies_resume_and_input_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extracted = root / "extracted"
            extracted.mkdir()
            entries = []
            for i, (name, data) in enumerate((("a.wtr", bytes(16)), ("b.dg", envelope(leaf())), ("c.dg_pv", bytes(20)))):
                (extracted / name).write_bytes(data)
                entries.append({"id": f"fixture-{i}", "baseline_id": "fixture", "original_path": name,
                                "extracted_path": name, "extension": Path(name).suffix, "size_bytes": len(data),
                                "content": {"status": "extracted", "sha256": hashlib.sha256(data).hexdigest()}})
            manifest = root / "manifest.jsonl"
            manifest.write_text("".join(json.dumps(e) + "\n" for e in entries))
            executable = root / "originals/sample.exe"
            executable.parent.mkdir()
            executable.write_bytes(b"synthetic-executable")
            exe_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
            manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
            profile = root / "profile.json"
            profile.write_text(json.dumps({"id": "fixture", "baseline_id": "fixture", "executable_sha256": exe_hash, "windows": [], "strings": []}))
            extraction = root / "extraction.json"
            extraction.write_text(json.dumps({"baseline_id": "fixture", "manifest": {"sha256": manifest_hash}}))
            wld_index = root / "wld-index.json"
            wld_index.write_text(json.dumps({"baseline_id": "fixture", "executable_sha256": exe_hash,
                                            "archive_manifest_sha256": manifest_hash, "sources": []}))
            args = SimpleNamespace(manifest=manifest, executable=executable, profile=profile,
                                   extraction_report=extraction, extracted_root=extracted, wld_index=wld_index,
                                   output_dir=root / "catalogs", report=root / "report.json")
            self.assertEqual(run(args), 1)
            report = json.loads(args.report.read_text())
            self.assertEqual((report["sources_examined"], report["sources_decoded"], len(report["errors"])), (3, 2, 1))
            self.assertEqual(report["errors"][0]["id"], "fixture-2")
            export = Path(report["sources"][0]["raw_catalog"]["path"])
            first_bytes = export.read_bytes()
            self.assertEqual(run(args), 1)
            self.assertEqual(export.read_bytes(), first_bytes)
            (extracted / "a.wtr").write_bytes(bytes(15))
            self.assertEqual(run(args), 1)
            self.assertEqual(json.loads(args.report.read_text())["sources_decoded"], 1)
            self.assertEqual(export.read_bytes(), first_bytes)
            manifest.write_text(manifest.read_text() + "\n")
            with self.assertRaisesRegex(FormatError, "baseline/manifest"):
                run(args)


if __name__ == "__main__":
    unittest.main()
