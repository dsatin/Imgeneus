"""Resource metadata bounds, map variants, and byte-preserving text structure."""

import io
import json
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from archive import FormatError
from resources import metadata, parse_world_config, parse_zon, wave_metadata


def chunk(tag, data):
    return tag + struct.pack("<I", len(data)) + data + bytes(len(data) % 2)


def wave():
    body = b"WAVE" + chunk(b"JUNK", b"x") + chunk(b"fmt ", struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)) + chunk(b"data", bytes(12))
    return b"RIFF" + struct.pack("<I", len(body)) + body


class ResourceTests(unittest.TestCase):
    def test_extracted_zon_first_and_last_records(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/zon-records.json").read_text())
        for sample in fixture["records"]:
            raw = bytes.fromhex(sample["raw_hex"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sample["record_sha256"])
            rows, _ = parse_zon(struct.pack("<ii", 5, 1) + raw)
            self.assertEqual(rows[0]["numeric_blocks"][0]["values"], sample["expected_values"])
            self.assertEqual(rows[0]["texts"][0]["raw_hex"], sample["expected_text_hex"])

    def test_zon_opaque_float_bits_and_unknown_text_are_preserved(self):
        layout = "<BBB" + "I" * 14 + "H"
        numeric = struct.pack(layout, 1, 2, 3, 0x7f800001, *([0] * 13), 47)
        payload = struct.pack("<ii", 5, 1) + numeric + struct.pack("<i", 2) + b"\xff\0"
        rows, header = parse_zon(payload)
        self.assertEqual(header["bytes_consumed"], len(payload))
        self.assertEqual(rows[0]["numeric_blocks"][0]["values"][3], 0x7f800001)
        self.assertEqual(rows[0]["texts"][0]["raw_hex"], "ff00")

    def test_zon_unverified_tag_count_truncation_and_extra_bytes(self):
        for payload in (struct.pack("<ii", 4, 0), struct.pack("<ii", 5, -1),
                        struct.pack("<ii", 5, 1) + bytes(64), struct.pack("<ii", 5, 0) + b"x"):
            with self.assertRaises(FormatError):
                parse_zon(payload)

    def test_config_duplicate_fields_leading_zero_and_line_endings(self):
        payload = b"#\xff\r\n[0]\r\nClick_top=0208\nClick_top=7\nMapNum=0"
        rows, sections = parse_world_config(payload)
        fields = sections[0]["fields"]
        self.assertEqual([f["integer_candidate"] for f in fields], [208, 7, 0])
        self.assertEqual(fields[0]["raw_value_hex"], "30323038")
        self.assertEqual(b"".join(bytes.fromhex(r["raw_hex"]) for r in rows), payload)
        self.assertEqual(rows[-1]["offset"], len(payload) - len(b"MapNum=0"))

    def test_wave_odd_chunk_padding_and_audio_metadata(self):
        payload = wave()
        info = wave_metadata(io.BytesIO(payload), len(payload))
        self.assertEqual(info["formats"][0]["sample_rate_hz"], 8000)
        self.assertEqual(info["audio_data_bytes"], 12)
        self.assertEqual(len(info["chunks"]), 3)

    def test_wave_extent_truncation_and_missing_format(self):
        for payload in (wave()[:-1], b"RIFF" + struct.pack("<I", 4) + b"WAVE",
                        b"RIFF" + struct.pack("<I", 12) + b"WAVEJUNK" + struct.pack("<I", 100)):
            with self.assertRaises(FormatError):
                wave_metadata(io.BytesIO(payload), len(payload))

    def test_explicit_unpadded_variant_preserves_following_chunk_offsets(self):
        body = b"WAVE" + chunk(b"fmt ", struct.pack("<HHIIHH", 85, 1, 8000, 1000, 1, 0))
        body += b"data" + struct.pack("<I", 1) + b"x" + chunk(b"LIST", bytes(4))
        payload = b"RIFF" + struct.pack("<I", len(body)) + body
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            path.write_bytes(payload)
            info = metadata(path, ".wav")
        self.assertEqual(info["layout_variant"], "observed_unpadded_chunks")
        self.assertIn("standard_layout_error", info)
        self.assertEqual(info["chunks"][-1]["offset"], 45)

    def test_bmp_signature_takes_precedence_over_dds_extension(self):
        header = bytearray(54)
        header[:2] = b"BM"
        struct.pack_into("<Iii", header, 14, 40, 32, -16)
        struct.pack_into("<H", header, 28, 24)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.dds"
            path.write_bytes(header)
            info = metadata(path, ".dds")
        self.assertEqual(info["kind"], "bmp")
        self.assertEqual(info["height_raw_i32"], -16)

    def test_invalid_dds_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.dds"
            path.write_bytes(b"DDS " + bytes(124))
            with self.assertRaises(FormatError):
                metadata(path, ".dds")


if __name__ == "__main__":
    unittest.main()
