#!/usr/bin/env python3
"""Record loose client file metadata without extracting or changing the client."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def inventory(client_dir, baseline_id):
    files = []
    skipped_symlinks = []
    for source in sorted(client_dir.rglob("*")):
        if source.is_symlink():
            skipped_symlinks.append(source.relative_to(client_dir).as_posix())
            continue
        if not source.is_file():
            continue
        before = source.stat()
        digest = hashlib.sha256()
        with source.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"Source changed during hashing: {source.name}")
        files.append({
            "path": source.relative_to(client_dir).as_posix(),
            "size_bytes": after.st_size,
            "sha256": digest.hexdigest(),
            "modified_at_utc": datetime.fromtimestamp(after.st_mtime, timezone.utc).isoformat(),
        })
    return {
        "schema_version": 1,
        "baseline_id": baseline_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_kind": "loose_client_files",
        "scope": "Files outside data.saf; internal archive inventory remains pending.",
        "hash_algorithm": "SHA-256",
        "generator": "tools/ep45-client/inventory.py",
        "file_count": len(files),
        "total_size_bytes": sum(entry["size_bytes"] for entry in files),
        "skipped_symlinks": skipped_symlinks,
        "files": files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-dir", type=Path, required=True)
    parser.add_argument("--baseline-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    client_dir = args.client_dir.resolve()
    output = args.output.resolve()
    if not client_dir.is_dir():
        parser.error("Client directory does not exist")
    if output == client_dir or client_dir in output.parents:
        parser.error("Output must be outside the client directory")
    manifest = inventory(client_dir, args.baseline_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {manifest['file_count']} loose files ({manifest['total_size_bytes']} bytes) in {output}")


if __name__ == "__main__":
    main()
