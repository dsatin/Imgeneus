"""Bounds, nested records, source discrepancies, and lossless raw storage."""

import struct
import unittest
import hashlib
import json
from pathlib import Path

from archive import FormatError
from extended_tables import QUEST_LAYOUT, RESULT_LAYOUT, SKILL_LAYOUT, normalize, parse_extended


def text(value=b""):
    return struct.pack("<i", len(value)) + value


def skill():
    return text(b"name\0") + text(b"\xff\0") + bytes(116)


def npc(group):
    payload = bytes(20 if group == 0 else 19) + text() * 2
    if group == 0:
        payload += struct.pack("<i", 2) + bytes([1, 7, 1, 7])
    if group == 1:
        payload += (struct.pack("<HIII", 1, 0x7f800001, 0x80000000, 0x3f800000) + text() + bytes(4)) * 3
    return payload + struct.pack("<iHH", 2, 7, 7) + bytes(4)


def npc_quest():
    payload = b"".join(struct.pack("<i", 1) + npc(group) for group in range(13))
    payload += struct.pack("<iH", 1, 7) + bytes(4) + bytes(8 * 65535)
    payload += struct.pack("<iH", 1, 17) + text(b"name\0") + text(b"summary\0")
    payload += bytes(87 + 26 * 3) + b"".join(text(bytes([i])) for i in range(7))
    return payload


class ExtendedTableTests(unittest.TestCase):
    def test_extracted_first_and_last_client_skill_records(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/skill-records.json").read_text())
        for sample in fixture["records"]:
            raw = bytes.fromhex(sample["raw_hex"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sample["source_record_sha256"])
            rows, _, issues, _ = parse_extended(struct.pack("<i", 1) + raw, "npc-skills")
            self.assertEqual(issues[0]["missing_records"], 8)
            self.assertEqual(rows[0]["numeric_blocks"][0]["values"], sample["expected_numeric_values"])
            self.assertEqual([t["raw_hex"] for t in rows[0]["texts"]], sample["expected_text_hex"])

    def test_skill_layout_and_nine_slots(self):
        self.assertEqual(struct.calcsize("<" + SKILL_LAYOUT), 116)
        rows, header, issues, _ = parse_extended(struct.pack("<i", 1) + skill() * 9, "skills")
        self.assertEqual(len(rows), 9)
        self.assertEqual(header["expected_records"], 9)
        self.assertFalse(issues)
        self.assertEqual(rows[-1]["group_record_ordinal"], 8)
        self.assertEqual(rows[0]["texts"][1]["raw_hex"], "ff00")

    def test_skill_missing_slots_are_explicit_not_success(self):
        rows, _, issues, _ = parse_extended(struct.pack("<i", 1) + skill() * 3, "skills")
        self.assertEqual(len(rows), 3)
        self.assertEqual(issues[0]["missing_records"], 6)

    def test_truncated_skill_inside_record_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_extended(struct.pack("<i", 1) + skill() * 3 + skill()[:-1], "skills")

    def test_skill_extra_bytes_are_rejected(self):
        with self.assertRaisesRegex(FormatError, "Unconsumed"):
            parse_extended(struct.pack("<i", 1) + skill() * 9 + b"x", "skills")

    def test_skill_negative_and_excessive_groups(self):
        for count in (-1, 1000000000):
            with self.assertRaises(FormatError):
                parse_extended(struct.pack("<i", count), "skills")

    def test_priest_four_sections_and_original_texts(self):
        section = struct.pack("<i", 1) + b"\xd2" + text(b"\xc0\xfc\0") + text(b"second\0")
        rows, header, issues, _ = parse_extended(section * 4, "priest-talk")
        self.assertEqual(header["section_counts"], [1] * 4)
        self.assertEqual(rows[0]["numeric_blocks"][0]["values"], [210])
        self.assertIsNone(rows[0]["texts"][0]["text"])
        self.assertFalse(issues)

    def test_priest_missing_section_and_invalid_lengths(self):
        for payload in (bytes(12), struct.pack("<iBi", 1, 0, -1) + bytes(20)):
            with self.assertRaises(FormatError):
                parse_extended(payload, "priest-talk")

    def test_npc_nested_arrays_float_bits_matrix_and_quests(self):
        self.assertEqual(struct.calcsize("<" + QUEST_LAYOUT), 87)
        self.assertEqual(struct.calcsize("<" + RESULT_LAYOUT), 26)
        rows, header, issues, matrix = parse_extended(npc_quest(), "npc-quest")
        self.assertEqual(len(rows), 14)
        self.assertFalse(issues)
        self.assertEqual(header["matrix"]["arrays"], 131072)
        self.assertEqual(len(matrix), 1)
        self.assertEqual(rows[0]["unknown_pairs"]["entries"][0]["values"], [1, 7])
        self.assertEqual(rows[0]["unknown_lists"][0]["entries"][1]["values"], [7])
        self.assertEqual(rows[1]["unknown_targets"][0]["numeric_blocks"][0]["values"][1], 0x7f800001)
        self.assertEqual(rows[-1]["numeric_blocks"][0]["values"], [17])
        self.assertEqual([t["raw_hex"] for t in rows[-1]["texts"][-7:]], [f"{i:02x}" for i in range(7)])

    def test_npc_truncated_nested_target_and_matrix(self):
        for payload in (npc_quest()[:100], npc_quest()[:10000], npc_quest()[:-1]):
            with self.assertRaises(FormatError):
                parse_extended(payload, "npc-quest")

    def test_matrix_invalid_list_count(self):
        payload = bytes(13 * 4) + struct.pack("<i", -1) + bytes(8 * 65535 + 8)
        with self.assertRaisesRegex(FormatError, "Invalid table count"):
            parse_extended(payload, "npc-quest")

    def test_normalized_ids_keep_section_boundaries_and_original_values(self):
        source = {"id": "fixture", "baseline_id": "test", "original_path": "test",
                  "source_sha256": "a" * 64, "decoded_sha256": "b" * 64}
        rows, _, _, _ = parse_extended((struct.pack("<iB", 1, 7) + text() * 2) * 4, "priest-talk")
        normalized = [normalize(row, source) for row in rows]
        self.assertEqual(len({r["id"] for r in normalized}), 4)
        self.assertTrue(all(r["client_id"] is None for r in normalized))
        self.assertEqual(normalized[0]["numeric_blocks"], rows[0]["numeric_blocks"])


if __name__ == "__main__":
    unittest.main()
