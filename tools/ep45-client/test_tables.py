#!/usr/bin/env python3
"""Bounded structural parsing and lossless handling of unresolved client data."""

import struct
import unittest

from archive import FormatError
from tables import LAYOUTS, parse_table


def text(value):
    return struct.pack("<i", len(value)) + value


class TableTests(unittest.TestCase):
    def test_variable_item_groups_and_original_identifier_bytes(self):
        numbers = bytearray(struct.calcsize("<" + LAYOUTS["items"]))
        numbers[:2] = bytes([2, 7])
        data = struct.pack("<iii", 2, 0, 1) + text(b"name\0") + text(b"description\0") + numbers
        records, header = parse_table(data, "items")
        self.assertEqual(header["group_record_counts"], [0, 1])
        self.assertEqual(records[0]["numeric_blocks"][0]["values"][:2], [2, 7])

    def test_invalid_text_keeps_raw_bytes_without_replacement(self):
        data = struct.pack("<i", 1) + text(b"\xff\0") + bytes(struct.calcsize("<" + LAYOUTS["mobs"]))
        record = parse_table(data, "mobs")[0][0]
        self.assertIsNone(record["texts"][0]["text"])
        self.assertEqual(record["texts"][0]["raw_hex"], "ff00")

    def test_cash_text_follows_all_24_numeric_pairs(self):
        numbers = bytes(struct.calcsize("<" + LAYOUTS["cash"]))
        data = struct.pack("<i", 1) + numbers + text(b"a\0\0") + text(b"b\0\0") + text(b"c\0\0")
        record = parse_table(data, "cash")[0][0]
        self.assertEqual(record["texts"][0]["offset"], 140)
        self.assertEqual(record["texts"][0]["trailing_zero_bytes"], 2)

    def test_fixed_guild_house_has_no_unconsumed_bytes(self):
        records, header = parse_table(bytes(648), "guild-house")
        self.assertEqual(len(records), 36)
        self.assertEqual(len(header["unknown_trailing_i32"]), 24)

    def test_kill_status_fixed_record_boundaries(self):
        records, _ = parse_table(struct.pack("<i", 2) + bytes(50), "kill-status")
        self.assertEqual([r["offset"] for r in records], [4, 29])

    def test_negative_or_excessive_counts(self):
        for count in (-1, 1000000000):
            with self.assertRaises(FormatError):
                parse_table(struct.pack("<i", count), "mobs")

    def test_truncation_of_a_variable_record(self):
        data = struct.pack("<i", 1) + text(b"name\0") + bytes(31)
        for end in (3, 8, len(data) - 1):
            with self.assertRaises(FormatError):
                parse_table(data[:end], "mobs")

    def test_negative_string_length(self):
        data = struct.pack("<ii", 1, -1) + bytes(31)
        with self.assertRaises(FormatError):
            parse_table(data, "mobs")

    def test_extra_bytes_are_not_silently_skipped(self):
        with self.assertRaisesRegex(FormatError, "Unconsumed"):
            parse_table(struct.pack("<i", 0) + b"unexpected", "mobs")


if __name__ == "__main__":
    unittest.main()
