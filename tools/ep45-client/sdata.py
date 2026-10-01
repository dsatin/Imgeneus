#!/usr/bin/env python3
"""Verify SData containers using SEED constants taken from the target client."""

import argparse
import ctypes
import ctypes.util
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import zlib

from archive import FormatError, SEED_SIGNATURE, sha256_file, target_path, write_json

TOOL_VERSION = "1.0.0"
MASK = 0xffffffff


class Seed:
    """SEED block transform with a client-provided expanded key and SS tables."""

    def __init__(self, key, tables):
        if len(key) != 128 or len(tables) != 4096:
            raise FormatError("Expected 128 key bytes and 4096 lookup-table bytes")
        self.key = struct.unpack("<32I", key)
        words = struct.unpack("<1024I", tables)
        self.tables = [words[i:i + 256] for i in range(0, 1024, 256)]
        self.native = None
        self.backend = "python"

    def g(self, value):
        return (self.tables[0][value & 255] ^ self.tables[1][(value >> 8) & 255] ^
                self.tables[2][(value >> 16) & 255] ^ self.tables[3][(value >> 24) & 255])

    def transform(self, block, decrypt=True):
        if len(block) != 16:
            raise FormatError("SEED requires exactly 16 bytes per block")
        left0, left1, right0, right1 = struct.unpack(">4I", block)
        indexes = range(30, -1, -2) if decrypt else range(0, 32, 2)
        for index in indexes:
            t0 = right0 ^ self.key[index]
            t1 = self.g((right1 ^ self.key[index + 1]) ^ t0)
            t0 = self.g((t0 + t1) & MASK)
            t1 = self.g((t1 + t0) & MASK)
            left0 ^= (t0 + t1) & MASK
            left1 ^= t1
            left0, left1, right0, right1 = right0, right1, left0, left1
        return struct.pack(">4I", right0, right1, left0, left1)

    def enable_native(self):
        """Use optional OpenSSL only after agreement with the reference transform."""
        name = ctypes.util.find_library("crypto")
        if not name:
            return
        try:
            library = ctypes.CDLL(name)
            for direction in ("decrypt", "encrypt"):
                function = getattr(library, "SEED_" + direction)
                function.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
                function.restype = None
            # Reserve enough storage for either 32-bit or 64-bit schedule words.
            # A differing ABI fails the reference comparison and is never selected.
            schedule = (ctypes.c_uint32 * 64)(*self.key)
            output = ctypes.create_string_buffer(16)
            for block in (bytes(16), bytes(range(16)), bytes([255]) * 16):
                for decrypt in (True, False):
                    function = library.SEED_decrypt if decrypt else library.SEED_encrypt
                    function(block, output, schedule)
                    if output.raw != self.transform(block, decrypt):
                        return
            self.native = library, schedule
            library.OpenSSL_version.argtypes = [ctypes.c_int]
            library.OpenSSL_version.restype = ctypes.c_char_p
            self.backend = library.OpenSSL_version(0).decode("ascii")
        except (OSError, AttributeError):
            self.native = None

    def blocks(self, data, decrypt=True):
        if len(data) % 16:
            raise FormatError("SEED payload is not aligned to 16 bytes")
        if self.native:
            library, schedule = self.native
            function = library.SEED_decrypt if decrypt else library.SEED_encrypt
            source = ctypes.create_string_buffer(data)
            output = ctypes.create_string_buffer(len(data))
            for offset in range(0, len(data), 16):
                function(ctypes.byref(source, offset), ctypes.byref(output, offset), schedule)
            return output.raw
        return b"".join(self.transform(data[i:i + 16], decrypt)
                        for i in range(0, len(data), 16))


def load_seed(executable, profile, backend="auto"):
    data = executable.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != profile["executable_sha256"]:
        raise FormatError("Executable hash does not match the crypto profile")
    segments = []
    for name in ("round_key", "lookup_tables"):
        source = profile[name]
        offset, length = source["file_offset"], source["size_bytes"]
        segment = data[offset:offset + length]
        if len(segment) != length or hashlib.sha256(segment).hexdigest() != source["sha256"]:
            raise FormatError(f"Client crypto segment does not match: {name}")
        segments.append(segment)
    seed = Seed(*segments)
    if backend == "auto":
        seed.enable_native()
    return seed


def decode_container(data, seed):
    if not data.startswith(SEED_SIGNATURE):
        return data, {"encrypted": False, "container_status": "not_applicable_with_evidence"}
    if len(data) < 64 or (len(data) - 64) % 16:
        raise FormatError("Truncated or misaligned SEED container")
    checksum, real_size = struct.unpack_from("<II", data, 40)
    checksum_offset = 40
    if checksum == 0:
        checksum, real_size = struct.unpack_from("<II", data, 44)
        checksum_offset = 44
    encoded = data[64:]
    if real_size > len(encoded) or len(encoded) - real_size > 15:
        raise FormatError("Declared SEED size does not match aligned payload size")
    padded = seed.blocks(encoded)
    decoded, padding = padded[:real_size], padded[real_size:]
    actual = zlib.crc32(decoded)
    if actual != checksum:
        raise FormatError(f"SEED CRC32 mismatch: stored={checksum}, computed={actual}")
    if encoded and (padded[:16] != seed.transform(encoded[:16]) or
                    padded[-16:] != seed.transform(encoded[-16:])):
        raise FormatError("Native and reference SEED transforms disagree")
    if seed.blocks(padded, decrypt=False) != encoded:
        raise FormatError("SEED decrypt/encrypt round trip differs from source bytes")
    return decoded, {"encrypted": True, "container_status": "statically_validated",
                     "signature_hex": data[:40].hex(), "header_hex": data[:64].hex(),
                     "checksum_offset": checksum_offset, "checksum_crc32": checksum,
                     "computed_crc32": actual, "decoded_size_bytes": real_size,
                     "alignment_padding_hex": padding.hex(), "round_trip_matches": True}


def preserve_output(path, data):
    """Create an output exclusively; verify existing outputs without replacement."""
    if path.exists():
        if path.is_symlink() or sha256_file(path) != hashlib.sha256(data).hexdigest():
            raise FormatError(f"Existing output differs or is a symlink: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.link(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def run(manifest, executable, profile_path, cache_dir, report_path, backend="auto"):
    profile = json.loads(profile_path.read_text())
    seed = load_seed(executable, profile, backend)
    source_root = manifest.resolve().parent
    destination = cache_dir.resolve()
    if destination == source_root or destination in source_root.parents:
        raise FormatError("Decoded output must use its own directory")
    for protected in (executable.resolve().parent, source_root / "extracted"):
        for output in (destination, report_path.resolve()):
            if output == protected or protected in output.parents:
                raise FormatError("Outputs must be outside original and extracted sources")
    with manifest.open(encoding="utf-8") as stream:
        entries = [json.loads(line) for line in stream]
    candidates = [entry for entry in entries if entry["extension"] == ".sdata"]
    if not candidates:
        raise FormatError("No SData entries in the archive manifest")
    if any(entry["baseline_id"] != profile["baseline_id"] for entry in candidates):
        raise FormatError("SData entries and crypto profile identify different baselines")
    results = []
    for entry in candidates:
        result = {"id": entry["id"], "baseline_id": entry["baseline_id"],
                  "original_path": entry["original_path"], "entry_kind": entry["entry_kind"],
                  "source_sha256": entry["content"].get("sha256"),
                  "saf_offset": entry["saf_offset"], "source_size_bytes": entry["size_bytes"],
                  "record_layout_status": "unknown"}
        try:
            if entry["content"]["status"] != "extracted":
                raise FormatError("Source entry has no verified extraction")
            source = source_root / "extracted" / entry["extracted_path"]
            if source.is_symlink() or source_root not in source.resolve().parents:
                raise FormatError("SData source leaves the extraction cache")
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != result["source_sha256"]:
                raise FormatError("SData content differs from its extraction manifest")
            if destination == source.resolve().parent or source.resolve().parent in destination.parents:
                raise FormatError("Decoded output must be outside extracted source directories")
            decoded, details = decode_container(data, seed)
            output = target_path(destination, entry["id"] + "/" + Path(entry["path"]).name)
            preserve_output(output, decoded)
            result.update(details)
            result.update({"status": "decoded", "decoded_path": str(output),
                           "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
                           "decoded_size_bytes": len(decoded)})
        except (OSError, ValueError) as exc:
            result.update({"status": "unknown", "error": str(exc)})
        results.append(result)
        print(f"{entry['id']} {entry['original_path']}: {result['status']}", flush=True)
    report = {"schema_version": 1, "baseline_id": candidates[0]["baseline_id"],
              "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "tool": {"path": "tools/ep45-client/sdata.py", "version": TOOL_VERSION,
                       "sha256": sha256_file(Path(__file__))},
              "archive_manifest_path": str(manifest.resolve()),
              "archive_manifest_sha256": sha256_file(manifest),
              "executable_path": str(executable.resolve()),
              "executable_sha256": profile["executable_sha256"],
              "crypto_profile_sha256": sha256_file(profile_path), "crypto_backend": seed.backend,
              "sources": results, "total_sources": len(results),
              "encrypted_sources": sum(r.get("encrypted", False) for r in results),
              "successful_sources": sum(r["status"] == "decoded" for r in results),
              "errors": sum("error" in r for r in results),
              "gameplay_records_decoded": 0}
    write_json(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--crypto-profile", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--backend", choices=("auto", "python"), default="auto")
    args = parser.parse_args()
    try:
        report = run(args.manifest, args.executable, args.crypto_profile,
                     args.output_dir, args.report, args.backend)
        return 1 if report["errors"] else 0
    except (OSError, ValueError) as exc:
        print(f"SData error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
