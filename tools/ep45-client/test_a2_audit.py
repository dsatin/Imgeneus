"""Exercise corrected widths, positional keys, and conservative gap analysis."""

import copy
import struct
import unittest

from a2_audit import compare_skills, encoding_candidates, lookup_key, parse_guild_house
from archive import FormatError


class AuditTests(unittest.TestCase):
    def test_guild_last_field_is_one_word(self):
        record = struct.pack("<BBBBBHHHHH", 1, 2, 3, 4, 5, 6, 7, 8, 9, 0x80ff)
        rows, headers = parse_guild_house(bytes(12) + record * 36 + bytes(96))
        self.assertEqual(rows[0]["numeric_blocks"][0]["values"][-1], 0x80ff)
        self.assertEqual(len(rows[0]["numeric_blocks"][0]["values"]), 10)
        self.assertEqual(rows[-1]["offset"], 537)
        self.assertEqual(len(headers["unknown_trailing_i32"]), 24)

    def test_guild_truncation_and_trailing_bytes_are_rejected(self):
        for payload in (bytes(647), bytes(649)):
            with self.assertRaises(FormatError):
                parse_guild_house(payload)

    def test_skill_differences_ignore_variable_offsets_and_keep_real_changes(self):
        left = {"group_ordinal": 0, "group_record_ordinal": 0, "offset": 4,
                "texts": [{"raw_hex": "6100"}], "numeric_blocks": [{"values": [1, 7]}]}
        right = copy.deepcopy(left)
        right["offset"] = 9
        self.assertEqual(compare_skills([left], [right])["changed_content_records"], 0)
        right["numeric_blocks"][0]["values"][1] = 8
        report = compare_skills([left], [right, right])
        self.assertEqual(report["changed_content_records"], 1)
        self.assertEqual(report["additional_supplemental_records"], 1)
        self.assertEqual(report["changes"][0]["different_numeric_field_ordinals"], [1])

    def test_positional_keys_do_not_use_placeholder_numeric_values(self):
        row = {"ordinal": 17, "group_ordinal": 2, "group_record_ordinal": 8,
               "numeric_blocks": [{"values": [0]}]}
        self.assertEqual(lookup_key(row, "npc-skills"), {"group_u16": 3, "slot_u8": 9})
        self.assertEqual(lookup_key(row, "mobs"), {"index_u16": 17})
        self.assertEqual(lookup_key(row, "items"), {"group_u8": 3, "record_u8": 9})

    def test_legacy_encoding_round_trip_is_only_a_candidate(self):
        raw = bytes.fromhex("c0fcbcb3")
        report = encoding_candidates({"nested": [{"encoding_status": "unknown", "raw_hex": raw.hex()}]})
        self.assertEqual(report["candidates"]["cp949"]["lossless_texts"], 1)
        self.assertEqual(report["client_conversion_encoding"], "unknown")
        self.assertEqual(report["candidates"]["cp949"]["status"], "inferred")


if __name__ == "__main__":
    unittest.main()
