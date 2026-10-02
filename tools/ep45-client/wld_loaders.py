#!/usr/bin/env python3
"""Reproduce bounded WLD loader evidence from the frozen executable."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from archive import FormatError, sha256_file, target_path, write_json
from baseline import pe_metadata
from sdata import preserve_output

TOOL_VERSION = "1.0.0"
EXECUTABLE_SHA256 = "98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48"
WINDOWS = (("wld-main", 0x451db0, 0x452960),
           ("wld-filename", 0x452960, 0x452d90),
           ("common-placements", 0x446890, 0x446b60),
           ("vani-placements", 0x446c80, 0x446f50),
           ("dungeon-placements", 0x447070, 0x447240),
           ("mani-placements", 0x41f9a0, 0x41fc00),
           ("object-placements", 0x525ba0, 0x5263b0),
           ("object-secondary", 0x5264d0, 0x526760),
           ("sound-lists", 0x52c250, 0x52c560),
           ("entity-lists", 0x527c00, 0x528c10),
           ("terrain-dispatch", 0x5916e0, 0x591730),
           ("terrain-grids", 0x5a1af0, 0x5a1c00),
           ("terrain-materials", 0x5a1490, 0x5a16c0))


def run(args):
    if sha256_file(args.executable) != EXECUTABLE_SHA256:
        raise FormatError("Executable does not match the analyzed WLD sample")
    for output in (args.output_dir.resolve(), args.report.resolve()):
        if output == args.executable.resolve().parent or args.executable.resolve().parent in output.parents:
            raise FormatError("Loader evidence outputs must be outside the source directory")
    pe = pe_metadata(args.executable)
    data = args.executable.read_bytes()
    windows = []
    for name, start, stop in WINDOWS:
        rva = start - pe["image_base"]
        section = next(s for s in pe["sections"] if s["rva"] <= rva and
                       stop - pe["image_base"] <= s["rva"] + s["file_size"])
        offset = section["file_offset"] + rva - section["rva"]
        target = target_path(args.output_dir.resolve(), name + ".asm")
        command = ["objdump", "-D", "-Mintel", f"--start-address={hex(start)}", f"--stop-address={hex(stop)}", str(args.executable)]
        preserve_output(target, subprocess.check_output(command))
        windows.append({"id": name, "start_va": hex(start), "stop_va": hex(stop), "start_rva": hex(rva),
                        "file_offset": hex(offset), "length": stop - start,
                        "source_bytes_sha256": hashlib.sha256(data[offset:offset + stop - start]).hexdigest(),
                        "disassembly_path": str(target), "disassembly_sha256": sha256_file(target),
                        "reproduction_arguments": command})
    report = {"id": "EP45-A3-WLD-LOADERS-001", "baseline_id": args.baseline_id,
              "executable_sha256": EXECUTABLE_SHA256, "image_base": hex(pe["image_base"]),
              "observation_date": datetime.now(timezone.utc).date().isoformat(),
              "project_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "tool": {"path": "tools/ep45-client/wld_loaders.py", "version": TOOL_VERSION,
                       "sha256": sha256_file(Path(__file__))},
              "objdump_version": subprocess.check_output(["objdump", "--version"], text=True).splitlines()[0],
              "address_mapping": "RVA = VA - PE image base; file offsets are calculated using PE section mappings. Windows are inspection bounds, not asserted function boundaries.",
              "windows": windows, "status": "statically_validated", "runtime_status": "unknown",
              "interpretations_reference": "docs/client-ep45/schemas/wld.md"}
    write_json(args.report, report)
    print(f"WLD loader evidence windows: {len(windows)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("executable", "output-dir", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--baseline-id", required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
