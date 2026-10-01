# Client inventory and extraction

Python 3 tools without external packages, .NET SDK, or Docker. Run from the
repository root. Client files are read-only sources; cache/reports are separate.

```bash
EP45_CLIENT_DIR='/home/dsatin/Games/Heroic/Prefixes/Shaiya EP 4.5/drive_c/RebirthEvolution'
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'

python3 tools/ep45-client/inventory.py --client-dir "$EP45_CLIENT_DIR" --baseline-id rebirth-evolution-ep45-98c7dd3a --output docs/client-ep45/catalogs/loose-files.current.json

python3 tools/ep45-client/baseline.py --client-dir "$EP45_CLIENT_DIR" --manifest docs/client-ep45/catalogs/loose-files.current.json --snapshot-dir "$EP45_CACHE/originals" --output docs/client-ep45/catalogs/baseline-evidence.json

python3 tools/ep45-client/archive.py extract --client-dir "$EP45_CACHE/originals" --output-dir "$EP45_CACHE" --report-dir docs/client-ep45/catalogs --baseline-id rebirth-evolution-ep45-98c7dd3a --expected-manifest docs/client-ep45/catalogs/loose-files.current.json

python3 tools/ep45-client/discover.py --manifest "$EP45_CACHE/archive-files.jsonl" --extraction-report docs/client-ep45/catalogs/extraction-report.json --output-dir docs/client-ep45/catalogs
```

`baseline.py` accepts `--original-game` for a pre-patch executable and
`--heroic-config` with `--game-id` for allowlisted runner options only.
Complete settings and potentially sensitive launch arguments are not published.
These optional arguments are not required to identify the available sample.

`archive.py inventory` indexes, validates, and hashes source intervals without
extracting. `extract` also compares each output with its SAF interval. Both
verify complete SAH/SAF hashes before/after. Unsupported encrypted indexes
produce explicit signature/count errors.

## Cache and resume

| Cache path | Contents |
| --- | --- |
| `originals/` | Frozen sample and original executable, when available |
| `extracted/tree/` | Main tree with original names/case |
| `extracted/duplicates/<ordinal>/` | Repeated entries, preserving the first |
| `extracted/supplemental/<ordinal>/` | Post-tree records, separate from active sources |
| `archive-files.jsonl` | Every entry, origin, offsets, hashes, classification, outcome |
| `archive-files.v1.jsonl` | Previous manifest before English status migration |
| `archive-folders.json` | Original folder tree/counts |
| `unreferenced-ranges.jsonl` | SAF intervals outside cataloged entries |

Cache is excluded from Git and Docker builds. The full manifest is about
20 MB; its hash/path and summaries are versioned in `docs/client-ep45/catalogs/`.

Rerun `extract` to resume. Existing outputs are read/verified without replacement.
Divergent content causes an error and remains intact. Interrupted runs retain
`.pending` manifests without promoting them; temporary files are not completed entries.

Original dates are in the external manifest. Extracted files carry extraction
dates; the observed SAH layout has no entry timestamps. Unproven fields retain
unknown semantics. All maintained metadata/prose use English; original client
text and bytes remain evidence in their original language.

## Tests

```bash
python3 -m unittest discover -s tools/ep45-client -p 'test_*.py'
```

Coverage: truncation, invalid counts/ranges/UTF-8, duplicate/case collisions,
nested intervals, traversal, file/folder conflicts, symlinks, corrupt outputs,
resume, and baseline mismatch. SData tests additionally cover header variants, size/alignment corruption,
CRC32, cipher round trip, profile mismatch, and preserving outputs. Table
tests cover variable/fixed structures, counts, text bytes, truncation, and
complete consumption. Three optional client-vector tests skip explicitly if
the frozen executable is unavailable; parser tests require no client files.


## A2: containers and structural records

```bash
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'

python3 tools/ep45-client/sdata.py --manifest "$EP45_CACHE/archive-files.jsonl" --executable "$EP45_CACHE/originals/game.exe" --crypto-profile docs/client-ep45/analysis/seed-profile.json --output-dir "$EP45_CACHE/decoded" --report docs/client-ep45/catalogs/sdata-containers.json

python3 tools/ep45-client/tables.py --containers docs/client-ep45/catalogs/sdata-containers.json --output-dir "$EP45_CACHE/catalogs/structures-v1" --report docs/client-ep45/catalogs/table-structures.json
```

Use `sdata.py --backend python` to require the standard-library reference
transform. Default `auto` tries the installed OpenSSL library, verifies it
against Python, and falls back without installing dependencies. To retain
both reports, use `--report "$EP45_CACHE/sdata-containers.python.json"` for
the reference run.

The crypto profile is bound to the executable hash; another client needs
its own analyzed profile. Raw source/constants remain in the executable.
`decoded/<entry-id>/` separates active/supplemental payloads.
`catalogs/structures-v1/<format>.raw.jsonl` and `<format>.jsonl` preserve record structure
and normalized provenance. Existing outputs are verified, never replaced;
use a new output directory for an intentional format/export revision.

All 13 SData containers have recorded outcomes. Five active structures are
decoded; four active layouts and supplemental semantics remain pending.
Unknown fields, IDs, signedness, and non-UTF-8 texts remain explicit. Record
counts are distinct from semantically validated formats and runtime coverage.
See [A2 evidence](../../docs/client-ep45/validation/phase-a2-initial.md).
