#!/usr/bin/env python3
"""Freeze loose client files and record PE/environment metadata without secrets."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import tempfile

from archive import CHUNK_SIZE, FormatError, sha256_file, target_path, write_json


def freeze(source, target, expected_hash):
    if sha256_file(source) != expected_hash:
        raise FormatError(f"Source differs from baseline: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha256_file(target) != expected_hash:
            raise FormatError(f"Frozen file differs from baseline: {target.name}")
        return
    fd, path = tempfile.mkstemp(prefix=".freeze-", dir=target.parent)
    temporary = Path(path)
    try:
        with os.fdopen(fd, "wb") as writer, source.open("rb") as reader:
            for block in iter(lambda: reader.read(CHUNK_SIZE), b""):
                writer.write(block)
        if sha256_file(temporary) != expected_hash:
            raise FormatError(f"Source changed while freezing: {source.name}")
        temporary.chmod(0o444)
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def pe_metadata(path):
    data = path.read_bytes()
    if data[:2] != b"MZ":
        raise FormatError("Not a PE executable")
    offset = struct.unpack_from("<I", data, 0x3c)[0]
    if data[offset:offset + 4] != b"PE\0\0":
        raise FormatError("Invalid PE header")
    machine, section_count, timestamp, _, _, optional_size, characteristics = struct.unpack_from("<HHIIIHH", data, offset + 4)
    optional = offset + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    if magic != 0x10b:
        raise FormatError("This baseline reader supports PE32 only")
    sections = []
    for ordinal in range(section_count):
        at = optional + optional_size + ordinal * 40
        raw_name, virtual_size, rva, size, file_offset = struct.unpack_from("<8sIIII", data, at)
        sections.append({"name": raw_name.rstrip(b"\0").decode("ascii"), "virtual_size": virtual_size,
                         "rva": rva, "file_offset": file_offset, "file_size": size})
    return {"machine": hex(machine), "format": "PE32", "coff_timestamp": timestamp,
            "coff_timestamp_utc": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
            "image_base": struct.unpack_from("<I", data, optional + 28)[0],
            "entry_point_rva": struct.unpack_from("<I", data, optional + 16)[0],
            "characteristics": characteristics, "sections": sections}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--original-game", type=Path)
    parser.add_argument("--heroic-config", type=Path)
    parser.add_argument("--game-id")
    args = parser.parse_args()
    client, snapshot, output = args.client_dir.resolve(), args.snapshot_dir.resolve(), args.output.resolve()
    if any(path == client or client in path.parents for path in (snapshot, output)):
        parser.error("Snapshot and report must be outside the client directory")
    manifest = json.loads(args.manifest.read_text())
    for record in manifest["files"]:
        source = target_path(client, record["path"])
        freeze(source, target_path(snapshot, record["path"]), record["sha256"])
    executable = snapshot / "game.exe"
    evidence = {
        "schema_version": 1, "baseline_id": manifest["baseline_id"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool": {"path": "tools/ep45-client/baseline.py", "version": "1.0.0", "sha256": sha256_file(Path(__file__))},
        "project_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "environment": {"os": platform.platform(), "python": platform.python_version()},
        "snapshot_files": len(manifest["files"]), "snapshot_directory": str(snapshot),
        "loose_manifest_sha256": sha256_file(args.manifest),
        "executable": {"sha256": sha256_file(executable), **pe_metadata(executable)},
        "patch": None,
    }
    if args.original_game:
        original_hash = sha256_file(args.original_game)
        freeze(args.original_game, target_path(snapshot, "game-original.exe"), original_hash)
        original, local = args.original_game.read_bytes(), executable.read_bytes()
        positions = [i for i, (a, b) in enumerate(zip(original, local)) if a != b]
        at = 0x2a9b84
        evidence["patch"] = {
            "original_sha256": original_hash, "modified_sha256": sha256_file(executable),
            "equal_file_sizes": len(original) == len(local), "changed_bytes": len(positions),
            "all_changes_inside_login_slot": all(at <= i < at + 16 for i in positions),
            "slot_offset": at, "slot_size_bytes": 16,
            "original_slot_hex": original[at:at + 16].hex(), "local_slot_hex": local[at:at + 16].hex(),
        }
    if args.heroic_config and args.game_id:
        selected = json.loads(args.heroic_config.read_text())[args.game_id]
        runner = selected.get("wineVersion", {})
        runner_dir = Path(runner.get("bin", "")).parent
        runner_version = runner_dir / "version"
        evidence["environment"]["heroic"] = {
            "runner_name": runner.get("name"), "runner_type": runner.get("type"),
            "runner_version_file": runner_version.read_text().strip() if runner_version.is_file() else None,
            "safe_options": {key: selected.get(key) for key in
                             ("enableEsync", "enableFsync", "useGameMode", "autoInstallDxvk", "autoInstallVkd3d", "enableWineWayland")},
        }
    write_json(output, evidence)
    print(f"Frozen and verified {len(manifest['files'])} loose files; report={output}")


if __name__ == "__main__":
    main()
