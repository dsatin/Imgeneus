#!/usr/bin/env python3
"""Capture bounded dungeon/water reader evidence from the identified executable."""

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess

from archive import FormatError, sha256_file, target_path, write_json
from baseline import pe_metadata
from sdata import preserve_output
from wld_loaders import EXECUTABLE_SHA256

TOOL_VERSION = "1.0.0"
WINDOWS = (("dungeon-loader", 0x5942c0, 0x59459a),
           ("dungeon-node", 0x593f80, 0x5941db),
           ("dungeon-group", 0x593de0, 0x593ee3),
           ("dungeon-patch", 0x593980, 0x593a6a),
           ("dungeon-auxiliary-mesh", 0x593160, 0x593260),
           ("dungeon-pages", 0x591f60, 0x592130),
           ("water-loader", 0x59ef20, 0x59f130),
           ("water-parameters", 0x59ed40, 0x59ef20),
           ("texture-loader", 0x59e790, 0x59e970),
           ("texture-buffer", 0x59add0, 0x59af30),
           ("archive-file-lookup", 0x59aaa0, 0x59abe0),
           ("map-dependencies", 0x451db0, 0x452960))
STRINGS = (("dungeon-page-pattern", 0x6bc9b0), ("resource-path-pattern", 0x6bc9c0),
           ("dungeon-texture-root", 0x6f8680), ("water-root", 0x6ad6f4))


def file_offset(pe, start, length):
    rva = start - pe["image_base"]
    for section in pe["sections"]:
        if section["rva"] <= rva and rva + length <= section["rva"] + section["file_size"]:
            return section["file_offset"] + rva - section["rva"]
    raise FormatError(f"Evidence window is outside mapped file bytes: {hex(start)}")


def run(args):
    if sha256_file(args.executable) != EXECUTABLE_SHA256:
        raise FormatError("Executable does not match the analyzed spatial-resource sample")
    source = args.executable.resolve().parent
    if any(p == source or source in p.parents for p in (args.output_dir.resolve(), args.report.resolve())):
        raise FormatError("Evidence outputs must be outside the source directory")
    pe, data = pe_metadata(args.executable), args.executable.read_bytes()
    windows, strings = [], []
    for name, start, stop in WINDOWS:
        offset = file_offset(pe, start, stop - start)
        target = target_path(args.output_dir.resolve(), name + ".asm")
        command = ["objdump", "-D", "-Mintel", f"--start-address={hex(start)}",
                   f"--stop-address={hex(stop)}", str(args.executable)]
        preserve_output(target, subprocess.check_output(command))
        windows.append({"id": name, "start_va": hex(start), "stop_va": hex(stop),
                        "start_rva": hex(start - pe["image_base"]), "file_offset": hex(offset),
                        "length": stop - start,
                        "source_bytes_sha256": hashlib.sha256(data[offset:offset + stop - start]).hexdigest(),
                        "disassembly_path": str(target), "disassembly_sha256": sha256_file(target),
                        "reproduction_arguments": command})
    for name, start in STRINGS:
        offset = file_offset(pe, start, 1)
        raw = data[offset:offset + 256].split(b"\0")[0] + b"\0"
        strings.append({"id": name, "start_va": hex(start),
                        "start_rva": hex(start - pe["image_base"]), "file_offset": hex(offset),
                        "length": len(raw), "raw_hex": raw.hex(), "text": raw[:-1].decode("ascii"),
                        "encoding_status": "ascii", "language": "unknown",
                        "source_bytes_sha256": hashlib.sha256(raw).hexdigest()})
    write_json(args.report, {
        "id": "EP45-A3-SPATIAL-LOADERS-001", "baseline_id": args.baseline_id,
        "executable_sha256": EXECUTABLE_SHA256, "image_base": hex(pe["image_base"]),
        "observation_date": datetime.now(timezone.utc).date().isoformat(),
        "project_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "tool": {"path": "tools/ep45-client/spatial_loaders.py", "version": TOOL_VERSION,
                 "sha256": sha256_file(Path(__file__))},
        "dependency_hashes": {name: sha256_file(Path(__file__).parent / name) for name in
                              ("wld_loaders.py", "baseline.py", "archive.py", "sdata.py")},
        "objdump_version": subprocess.check_output(["objdump", "--version"], text=True).splitlines()[0],
        "address_mapping": "RVA = VA - PE image base; offsets use PE section mappings. Windows are inspection bounds, not asserted function boundaries.",
        "windows": windows, "strings": strings, "status": "statically_validated",
        "runtime_status": "unknown", "interpretations_reference": "docs/client-ep45/schemas/spatial-resources.md"})
    print(f"Spatial loader evidence: {len(windows)} windows; {len(strings)} strings")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("executable", "output-dir", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--baseline-id", required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
