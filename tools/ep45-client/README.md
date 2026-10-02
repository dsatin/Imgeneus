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

All 13 SData containers have recorded outcomes. The initial tool decoded five
active structures; the extended tool covers the remaining four active sources
and the supplemental Skill separately.
Unknown fields, IDs, signedness, and non-UTF-8 texts remain explicit. Record
counts are distinct from semantically validated formats and runtime coverage.
See [A2 evidence](../../docs/client-ep45/validation/phase-a2-initial.md).

## A2: skills, dialogue, NPCs, and quests

```bash
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'
python3 tools/ep45-client/extended_tables.py --containers docs/client-ep45/catalogs/sdata-containers.json --output-dir "$EP45_CACHE/catalogs/extended-v1" --report docs/client-ep45/catalogs/extended-table-structures.json
```

The identified active Skill file lacks six terminal records expected by the
executable. This command deliberately exits **1**, while publishing complete
recovered records and an explicit discrepancy; it does not hide the failure
or substitute supplemental data. The other three active sources decode
completely. A repeated run verifies existing exports without replacement.
Raw/normalized exports are separated by archive entry ID. The matrix export
is sparse; all 65,536 cells/two arrays per cell remain in coverage denominators.
`fixtures/skill-records.json` contains small first/last NpcSkill source spans
with provenance and hashes. Tests need no installed client for these fixtures.
See [schema](../../docs/client-ep45/schemas/extended-sdata-tables.md) and
[validation](../../docs/client-ep45/validation/phase-a2-extended.md).

Executable inspection is read-only. Reproduce the bounded windows with
`objdump -d -Mintel` and the start/stop addresses and source parameters in
[loader evidence](../../docs/client-ep45/analysis/extended-table-loaders.json).
Verify the executable hash and PE address mapping before applying any offsets.
These tools require no database credentials, running server, SDK, or network.

## A2: remaining-gap audit

```bash
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'
python3 tools/ep45-client/a2_audit.py --containers docs/client-ep45/catalogs/sdata-containers.json --initial docs/client-ep45/catalogs/table-structures.json --extended docs/client-ep45/catalogs/extended-table-structures.json --profile docs/client-ep45/analysis/table-lookup-profile.json --executable "$EP45_CACHE/originals/game.exe" --output-dir "$EP45_CACHE/catalogs/audit-v2" --report docs/client-ep45/validation/a2-audit.json
```

The audit pins executable windows and verifies input catalog hashes. It creates
separate lookup-enriched catalogs and a corrected GuildHouse word layout,
compares active/supplemental Skill contents by value rather than shifted offsets,
and reports strict encoding round trips as candidates. It does not declare
remaining A2 gaps resolved. See [pending work](../../docs/client-ep45/validation/a2-pending.md).

## A3: resource catalogs and map metadata

```bash
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'
python3 tools/ep45-client/resources.py --manifest "$EP45_CACHE/archive-files.jsonl" --extraction-report docs/client-ep45/catalogs/extraction-report.json --extracted-root "$EP45_CACHE/extracted" --output-dir "$EP45_CACHE/catalogs/resources-v4" --report docs/client-ep45/catalogs/resource-catalogs.json --executable-sha256 98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48
```

This verifies every source size/hash, preserves all entries/errors, and creates
full/UI/audio/map catalogs plus ZON records. Media metadata is separate from
payload decoding. Two explicitly labeled unpadded WAV layouts retain their
standard-layout failures; their playback is untested. WorldMap.cfg keeps raw
lines and duplicate fields; MapNum-to-WLD filename matches remain inferred.
The command succeeds with zero reader/file errors for this identified sample.
Existing exports are verified without replacement; revisions use new folders.

Small extracted first/last ZON fixtures in `fixtures/zon-records.json` run
without the installation. See [resource schema](../../docs/client-ep45/schemas/resource-metadata.md)
and [A3 validation](../../docs/client-ep45/validation/phase-a3-resources.md).

## A3: WLD readers and map-content catalogs

```bash
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'
python3 tools/ep45-client/wld_loaders.py --executable "$EP45_CACHE/originals/game.exe" --baseline-id rebirth-evolution-ep45-98c7dd3a --output-dir "$EP45_CACHE/analysis/wld-v1" --report docs/client-ep45/analysis/wld-loaders.json
python3 tools/ep45-client/wld.py --manifest "$EP45_CACHE/archive-files.jsonl" --extraction-report docs/client-ep45/catalogs/extraction-report.json --extracted-root "$EP45_CACHE/extracted" --executable "$EP45_CACHE/originals/game.exe" --profile docs/client-ep45/analysis/wld-loaders.json --output-dir "$EP45_CACHE/catalogs/wld-v3" --report docs/client-ep45/catalogs/wld-catalogs.json
python3 -m unittest discover -s tools/ep45-client -p 'test_*.py'
```

Both tools are version 1.0.0. Loader extraction requires local `objdump` and
binds 13 bounded windows through PE section mappings and source byte hashes.
The parser verifies that profile, the executable hash, and archive manifest.
It decodes 86/86 WLD structures with complete consumption and saved-export
reconstruction. Raw JSON and relative hashed grid blobs reconstruct the source;
normalized JSONL catalogs records and candidate asset/name-index relationships.
Every failure remains in the denominator and produces exit status 1.

Grid payload semantics, original entity keys, units, portal/NPC rules, and
runtime behavior remain unknown. Empty/missing resource links remain present.
Object0's 76/152-byte nonempty variants have static/synthetic evidence only.
Existing export content is verified, never replaced; changed layouts require
a new directory. Reports may update generation metadata; structured exports
are deterministic. The earlier local WLD probe outputs remain untracked cache.

Three complete small source fixtures in `fixtures/wld-samples.json` run without
the installation. See [format/field dictionary](../../docs/client-ep45/schemas/wld.md),
[catalog index](../../docs/client-ep45/catalogs/wld-catalogs.json), and
[validation](../../docs/client-ep45/validation/phase-a3-wld.md).
