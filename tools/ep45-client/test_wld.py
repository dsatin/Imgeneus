"""Exercise source fixtures, nested WLD counts, variants, and lossless exports."""

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from archive import FormatError
from wld import WldReader, bind_profile, parse_wld, rebuild_wld, resource_targets


def samples():
    return json.loads((Path(__file__).parent / "fixtures/wld-samples.json").read_text())["samples"]


def empty_dungeon():
    return bytes.fromhex(samples()[0]["raw_hex"])


def replace_empty_array(data, section, count, records):
    header = next(p for p in parse_wld(data)["parts"] if p["section"] == section and p["kind"] == "count")
    assert header["value"] == 0
    offset = header["offset"]
    return data[:offset] + struct.pack("<i", count) + records + data[offset + 4:]


class WldTests(unittest.TestCase):
    def test_extracted_samples_counts_offsets_and_round_trip(self):
        for sample in samples():
            with self.subTest(source=sample["source_path"]):
                data = bytes.fromhex(sample["raw_hex"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), sample["source_sha256"])
                document = parse_wld(data)
                self.assertEqual(document["counts"], sample["expected_counts"])
                self.assertEqual(rebuild_wld(document), data)
                self.assertEqual(document["parts"][-1]["offset"] + 44, len(data))

    def test_every_truncated_prefix_and_extra_byte_are_rejected(self):
        data = empty_dungeon()
        for length in range(len(data)):
            with self.subTest(length=length), self.assertRaises(FormatError):
                parse_wld(data[:length])
        with self.assertRaises(FormatError):
            parse_wld(data + b"x")

    def test_invalid_signature_counts_and_extent_are_rejected(self):
        for value in (-1, 0x7fffffff):
            payload = replace_empty_array(empty_dungeon(), "shape-names", value, b"")
            with self.assertRaises(FormatError):
                parse_wld(payload)
        for data in (b"NEW\0" + empty_dungeon()[4:],
                     b"FLD\0" + struct.pack("<i", -2), b"FLD\0" + struct.pack("<i", 3)):
            with self.assertRaises(FormatError):
                parse_wld(data)

    def test_mani_44_byte_variant_preserves_both_indices_and_float_bits(self):
        values = [0xffffffff, 0, 0x7f800001] + [0] * 8
        record = struct.pack("<11I", *values)
        data = replace_empty_array(empty_dungeon(), "mani-placements", 1, record)
        part = next(p for p in parse_wld(data)["parts"] if p["section"] == "mani-placements" and p["kind"] == "record")
        self.assertEqual(part["size_bytes"], 44)
        self.assertEqual(part["numeric_blocks"][0]["values"], values)
        self.assertEqual(rebuild_wld(parse_wld(data)), data)
        with self.assertRaises(FormatError):
            parse_wld(replace_empty_array(empty_dungeon(), "mani-placements", 1, record[:40]))

    def test_object_single_and_paired_records_have_distinct_counts(self):
        data = replace_empty_array(empty_dungeon(), "object0-placements", 1, bytes(76))
        data = replace_empty_array(data, "object0-pairs", 2, bytes(304))
        document = parse_wld(data)
        pairs = [p for p in document["parts"] if p["section"] == "object0-pairs" and p["kind"] == "record"]
        self.assertEqual([p["size_bytes"] for p in pairs], [152, 152])
        self.assertEqual(document["counts"]["object0-placements"], 1)
        self.assertEqual(rebuild_wld(document), data)

    def test_portal_248_byte_text_boundary_and_padding_are_preserved(self):
        second_text = b"\xff\0" + b"p" * 246
        record = bytes(28) + bytes(256) + second_text + struct.pack("<6I", 1, 2, 3, 4, 5, 6)
        data = replace_empty_array(empty_dungeon(), "portals", 1, record)
        portal = next(p for p in parse_wld(data)["parts"] if p["section"] == "portals" and p["kind"] == "record")
        self.assertEqual(portal["texts"][1]["size_bytes"], 248)
        self.assertEqual(portal["texts"][1]["encoding_status"], "unknown")
        self.assertEqual(portal["texts"][1]["padding_nonzero_bytes"], 246)
        self.assertEqual(portal["numeric_blocks"][1]["values"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(rebuild_wld(parse_wld(data)), data)

    def test_npc_aggregate_includes_children_and_rejects_overrun(self):
        record = struct.pack("<6Ii6I", 1, 2, 3, 4, 5, 6, 2, 7, 8, 9, 10, 11, 12)
        data = replace_empty_array(empty_dungeon(), "npc-aggregate", 3, record)
        document = parse_wld(data)
        self.assertEqual(document["counts"]["npcs"], 1)
        self.assertEqual(document["counts"]["npc-points"], 2)
        self.assertEqual(rebuild_wld(document), data)
        with self.assertRaises(FormatError):
            parse_wld(replace_empty_array(empty_dungeon(), "npc-aggregate", 2, record))

    def test_nested_region_groups_and_sound_members_are_consumed(self):
        data = replace_empty_array(empty_dungeon(), "region-groups", 2,
                                   struct.pack("<i9Ii", 1, *range(9), 0))
        data = replace_empty_array(data, "sound-zones", 1, bytes(24) + struct.pack("<i2I", 2, 3, 4))
        document = parse_wld(data)
        self.assertEqual(document["counts"]["region-group-0"], 1)
        self.assertEqual(document["counts"]["region-group-1"], 0)
        self.assertEqual(document["counts"]["sound-zone-0-members"], 2)
        self.assertEqual(rebuild_wld(document), data)

    def test_field_grids_and_exported_blob_integrity(self):
        data = b"FLD\0" + struct.pack("<i", 4) + bytes(27) + bytes(4) + empty_dungeon()[4:-44] + bytes(768) + empty_dungeon()[-44:]
        document = parse_wld(data)
        grids = [p for p in document["parts"] if p["section"].startswith("grid-")]
        self.assertEqual([p["size_bytes"] for p in grids], [18, 9])
        self.assertEqual(rebuild_wld(document), data)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for part in document["parts"]:
                if part["kind"] == "blob":
                    part["blob_path"] = part["section"] + ".bin"
                    (root / part["blob_path"]).write_bytes(part.pop("data"))
            saved = json.loads(json.dumps(document))
            self.assertEqual(rebuild_wld(saved, root), data)
            (root / "grid-u8.bin").write_bytes(bytes(8) + b"x")
            with self.assertRaises(FormatError):
                rebuild_wld(saved, root)

    def test_record_bounds_unknown_text_and_nonterminated_string(self):
        reader = WldReader(b"a" * 256)
        row = reader.record("fixture", fields=(("text", 256),))
        self.assertFalse(row["texts"][0]["nul_terminated"])
        with self.assertRaises(FormatError):
            WldReader(bytes(247)).record("fixture", fields=(("text", 248),))

    def test_resource_links_preserve_duplicate_targets_and_reject_traversal(self):
        paths = {"entity/tree/a.3dc": ["tree-2", "tree-1"], "sound/back/b.wav": ["tree-3"]}
        self.assertEqual(resource_targets("A.3DC", ["entity/tree"], paths), ["tree-1", "tree-2"])
        self.assertEqual(resource_targets("b.wav", ["Sound/music", "Sound/back"], paths), ["tree-3"])
        for name in ("../a.3dc", "/a.3dc", "C:\\a.3dc", "sub/../a.3dc", None):
            self.assertEqual(resource_targets(name, ["entity/tree"], paths), [])

    def test_executable_profile_binds_source_and_window_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.exe"
            source.write_bytes(b"abcdef")
            profile = {"executable_sha256": hashlib.sha256(b"abcdef").hexdigest(),
                       "windows": [{"id": "fixture", "file_offset": "0x1", "length": 3,
                                    "source_bytes_sha256": hashlib.sha256(b"bcd").hexdigest()}]}
            bind_profile(source, profile)
            profile["windows"][0]["source_bytes_sha256"] = "0" * 64
            with self.assertRaises(FormatError):
                bind_profile(source, profile)
            source.write_bytes(b"ABCDEF")
            with self.assertRaises(FormatError):
                bind_profile(source, profile)


if __name__ == "__main__":
    unittest.main()
