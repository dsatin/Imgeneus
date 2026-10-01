#!/usr/bin/env python3
"""SData corruption, provenance, output preservation, and client-vector checks."""

import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from archive import FormatError, SEED_SIGNATURE
from sdata import decode_container, load_seed, preserve_output, Seed

ROOT = Path(__file__).resolve().parents[2]


class IdentitySeed:
    def blocks(self, data, decrypt=True):
        return data

    def transform(self, data, decrypt=True):
        return data


def container(payload, shifted=False, padding_byte=0):
    header = SEED_SIGNATURE + (bytes(4) if shifted else b"")
    header += struct.pack("<II", zlib.crc32(payload), len(payload))
    header = header.ljust(64, b"\0")
    return header + payload + bytes([padding_byte]) * (-len(payload) % 16)


class ContainerTests(unittest.TestCase):
    def test_plain_source_stays_identical(self):
        self.assertEqual(decode_container(b"plain source", None)[0], b"plain source")

    def test_both_header_positions(self):
        for shifted in (False, True):
            decoded, details = decode_container(container(b"payload", shifted), IdentitySeed())
            self.assertEqual(decoded, b"payload")
            self.assertEqual(details["checksum_offset"], 44 if shifted else 40)

    def test_truncated_header(self):
        with self.assertRaises(FormatError):
            decode_container(SEED_SIGNATURE, IdentitySeed())

    def test_misaligned_payload(self):
        with self.assertRaises(FormatError):
            decode_container(container(b"payload")[:-1], IdentitySeed())

    def test_size_outside_payload(self):
        data = bytearray(container(b"payload"))
        struct.pack_into("<I", data, 44, 100)
        with self.assertRaises(FormatError):
            decode_container(data, IdentitySeed())

    def test_excess_alignment_is_not_ignored(self):
        with self.assertRaises(FormatError):
            decode_container(container(b"payload") + bytes(16), IdentitySeed())

    def test_checksum_corruption(self):
        data = bytearray(container(b"payload"))
        data[64] ^= 1
        with self.assertRaisesRegex(FormatError, "CRC32"):
            decode_container(data, IdentitySeed())

    def test_nonzero_padding_is_preserved(self):
        _, details = decode_container(container(b"payload", padding_byte=3), IdentitySeed())
        self.assertEqual(details["alignment_padding_hex"], "03" * 9)

    def test_cipher_round_trip_is_required(self):
        class IncorrectEncoder(IdentitySeed):
            def blocks(self, data, decrypt=True):
                return data if decrypt else bytes(len(data))
        with self.assertRaisesRegex(FormatError, "round trip"):
            decode_container(container(b"payload"), IncorrectEncoder())

    def test_seed_lengths_are_checked(self):
        with self.assertRaises(FormatError):
            Seed(bytes(127), bytes(4096))
        with self.assertRaises(FormatError):
            Seed(bytes(128), bytes(4096)).blocks(bytes(15))

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "data"
            preserve_output(path, b"original")
            preserve_output(path, b"original")
            with self.assertRaises(FormatError):
                preserve_output(path, b"replacement")
            self.assertEqual(path.read_bytes(), b"original")

    def test_output_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source"
            path.write_bytes(b"original")
            link = Path(directory) / "link"
            link.symlink_to(path)
            with self.assertRaises(FormatError):
                preserve_output(link, b"original")


class ClientVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = ROOT / ".client-ep45-cache/rebirth-evolution-ep45-98c7dd3a/originals/game.exe"
        if not cls.executable.exists():
            raise unittest.SkipTest("Optional client-vector checks require the local frozen executable")
        cls.profile = json.loads((ROOT / "docs/client-ep45/analysis/seed-profile.json").read_text())
        cls.fixture = json.loads((ROOT / "tools/ep45-client/fixtures/seed-cash-block.json").read_text())

    def test_client_block_in_reference_and_optional_native_backend(self):
        encoded = bytes.fromhex(self.fixture["ciphertext_hex"])
        decoded = bytes.fromhex(self.fixture["plaintext_hex"])
        for backend in ("python", "auto"):
            seed = load_seed(self.executable, self.profile, backend)
            self.assertEqual(seed.blocks(encoded), decoded)
            self.assertEqual(seed.blocks(decoded, decrypt=False), encoded)

    def test_wrong_executable_is_rejected(self):
        profile = {**self.profile, "executable_sha256": "0" * 64}
        with self.assertRaisesRegex(FormatError, "Executable hash"):
            load_seed(self.executable, profile)

    def test_wrong_constant_segment_is_rejected(self):
        profile = {**self.profile, "round_key": {**self.profile["round_key"], "sha256": "0" * 64}}
        with self.assertRaisesRegex(FormatError, "crypto segment"):
            load_seed(self.executable, profile)


if __name__ == "__main__":
    unittest.main()
