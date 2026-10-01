"""Integrity and containment checks for the archive extractor (synthetic data)."""

import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import archive


def name(value):
    data = value.encode() + b"\0"
    return struct.pack("<i", len(data)) + data


def record(path, offset, size):
    return name(path) + struct.pack("<qii", offset, size, 0)


def sah(records, declared=None, trailing=b""):
    header = b"SAH" + struct.pack("<ii", 0, len(records) if declared is None else declared) + bytes(40)
    return header + name("") + struct.pack("<i", len(records)) + b"".join(records) + struct.pack("<i", 0) + trailing


class ArchiveChecks(unittest.TestCase):
    def test_tree_and_trailing_records_remain_separate(self):
        tail = struct.pack("<i", 1) + record("old.SData", 1, 2) + struct.pack("<i", 0)
        index = archive.parse_sah(sah([record("active.SData", 0, 1)], trailing=tail))
        self.assertEqual(index["tree_file_count"], 1)
        self.assertEqual(index["supplemental"][0]["entry_kind"], "supplemental")
        self.assertEqual(index["trailing"]["semantics"], "unknown")

    def test_opaque_tail_is_reported_without_inventing_entries(self):
        index = archive.parse_sah(sah([], trailing=b"opaque"))
        self.assertEqual(index["trailing"]["size_bytes"], 6)
        self.assertEqual(index["supplemental"], [])
        self.assertIsNotNone(index["trailing"]["candidate_error"])

    def test_truncation_and_invalid_counts_fail(self):
        for data in [b"SAH", sah([record("x", 0, 2)])[:-1],
                     b"SAH" + struct.pack("<ii", 0, -1) + bytes(40)]:
            with self.subTest(data=data[:20]), self.assertRaises(archive.FormatError):
                archive.parse_sah(data)

    def test_invalid_utf8_does_not_get_replaced_silently(self):
        data = b"SAH" + struct.pack("<ii", 0, 0) + bytes(40) + struct.pack("<i", 2) + b"\xff\0"
        with self.assertRaises(archive.FormatError):
            archive.parse_sah(data)

    def test_count_mismatch_and_out_of_bounds_are_visible(self):
        index = archive.parse_sah(sah([record("x", 4, 7)], declared=2))
        report = archive.validate_index(index, 10)
        self.assertEqual(report["issues"][0]["kind"], "count_mismatch")
        self.assertEqual(report["invalid_entries"], ["tree-000000"])

    def test_nested_and_identical_overlaps_are_all_reported(self):
        index = archive.parse_sah(sah([record("large", 0, 10), record("inside", 2, 3),
                                      record("same", 2, 3), record("end", 8, 2)]))
        report = archive.validate_index(index, 10)
        self.assertEqual(len(report["tree_overlaps"]), 4)

    def test_three_duplicates_and_case_variants_are_preserved(self):
        index = archive.parse_sah(sah([record("same", 0, 1), record("same", 1, 1),
                                      record("same", 2, 1), record("SAME", 3, 1)]))
        report = archive.validate_index(index, 4)
        self.assertEqual(len(report["duplicates"][0]["ids"]), 3)
        self.assertEqual(len(report["case_collisions"][0]["ids"]), 4)
        self.assertEqual(len({e["extracted_path"] for e in index["entries"]}), 4)

    def test_unsafe_archive_paths_are_rejected(self):
        for path in ["../outside", "/absolute", "C:\\outside", "a/../../escape", "a//b", "a\0b"]:
            with self.subTest(path=path), self.assertRaises(archive.FormatError):
                archive.normalized_path(path)

    def test_file_directory_conflict_is_not_written(self):
        index = archive.parse_sah(sah([record("a", 0, 1), record("a/b", 1, 1)]))
        checks = archive.validate_index(index, 2)
        self.assertEqual(checks["invalid_entries"], ["tree-000001"])

    def test_extract_resume_and_corruption_never_replace_raw_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client, output, reports = root / "client", root / "cache", root / "reports"
            client.mkdir()
            (client / "data.sah").write_bytes(sah([record("a", 0, 3), record("empty", 3, 0)]))
            (client / "data.saf").write_bytes(b"abc")
            first = archive.run(client, output, reports, "fixture", True)
            self.assertEqual(first["counts"], {"tree:extracted": 2})
            self.assertEqual((output / "extracted/tree/a").read_bytes(), b"abc")
            initial_mtime = (output / "extracted/tree/a").stat().st_mtime_ns
            second = archive.run(client, output, reports, "fixture", True)
            self.assertEqual(second["manifest"]["sha256"], first["manifest"]["sha256"])
            self.assertEqual((output / "extracted/tree/a").stat().st_mtime_ns, initial_mtime)
            (output / "extracted/tree/a").write_bytes(b"bad")
            third = archive.run(client, output, reports, "fixture", True)
            self.assertEqual(len(third["errors"]), 1)
            self.assertEqual((output / "extracted/tree/a").read_bytes(), b"bad")

    def test_symlink_destination_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            cache = root / "cache"
            cache.mkdir()
            (cache / "tree").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(archive.FormatError):
                archive.target_path(cache, "tree/asset")
            self.assertFalse((outside / "asset").exists())

    def test_truncated_saf_does_not_leave_a_completed_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            index = archive.parse_sah(sah([record("asset", 0, 6)]))
            archive.validate_index(index, 6)
            with self.assertRaises(archive.FormatError):
                archive.process_entry(io.BytesIO(b"short"), index["entries"][0], Path(directory), True)
            self.assertFalse((Path(directory) / "tree/asset").exists())
            self.assertFalse(list(Path(directory).rglob(".extract-*")))

    def test_baseline_mismatch_and_source_output_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = root / "client"
            client.mkdir()
            (client / "data.sah").write_bytes(sah([]))
            (client / "data.saf").write_bytes(b"")
            with self.assertRaises(archive.FormatError):
                archive.run(client, client / "bad", root / "reports", "fixture", True)
            expected = root / "baseline.json"
            expected.write_text(json.dumps({"files": [{"path": "data.sah", "sha256": "0" * 64}]}))
            with self.assertRaises(archive.FormatError):
                archive.run(client, root / "cache", root / "reports", "fixture", True, expected)
            self.assertFalse((root / "cache").exists())


if __name__ == "__main__":
    unittest.main()
