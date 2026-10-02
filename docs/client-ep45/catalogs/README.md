# Catalogs and manifests

`loose-files.json` identifies the installation's loose files through metadata
and hashes only. It contains no settings contents, dumps, or executable bytes
and does not represent the internal SAF inventory.

`loose-files.current.json` records A0/A1 configuration; the prior manifest is
preserved. Only `CONFIG.INI` changed. The full internal index contains 23,570
records and stays in cache (~20 MB), indexed by `extraction-report.json`.

Current outputs: `baseline-evidence.json`, `extraction-report.json`,
`data-sources.json`, `map-files.json`, and `asset-summary.json`. Those A1 discovery outputs identify sources/assets rather than decoded
records. A2 adds `sdata-containers.json` and `table-structures.json`; the latter
indexes five raw/normalized bulk record catalogs and unresolved layouts.
`extended-table-structures.json` indexes the subsequent Skill/NpcSkill,
PriestTalk, NPC/quest, and sparse matrix exports, including the active Skill
count discrepancy and the separate supplemental Skill outcome.
`resource-catalogs.json` indexes A3 catalogs for all 23,570 source entries,
UI/audio/map groups, 35 ZON records, candidate map links, and explicit WAV
source anomalies. Resource file counts are not entity/action coverage.
`wld-catalogs.json` indexes subsequent body extraction of all 86 WLD sources,
491,518 structural rows, 5,937 filename links, and exact reconstruction.
Its raw JSON/normalized JSONL and hashed grid blobs remain in cache. Grid
semantics and runtime behavior are pending; the original resource metadata
index remains a historical snapshot. See [WLD validation](../validation/phase-a3-wld.md).
Discovery header flags describe the earlier A1 inventory; the A2 container
report records subsequent checksum/decryption validation.

`spatial-catalogs.json` indexes the subsequent 47 DG/three WTR structural
exports and all 12 failed DG_PV candidates. It retains 193,059 structural
parts, complete typed mesh arrays, water parameters/texts, and 3,552 dependency
links. Raw JSON/normalized JSONL stay in `catalogs/spatial-v2/` cache, with
source/export hashes in the versioned index. Exact links, same-stem DDS
hypotheses, empty names, and missing generated pages are counted separately.
See [validation](../validation/phase-a3-spatial.md).

Reproduce from the repository root:

```bash
python3 tools/ep45-client/inventory.py --client-dir '/path/to/RebirthEvolution' --baseline-id rebirth-evolution-ep45-98c7dd3a --output docs/client-ep45/catalogs/loose-files.current.json
```

The tool streams hashes, refuses output inside the client, detects source
size/date changes, and records skipped symlinks. Generation dates vary; IDs,
paths, and hashes must remain identical for unchanged sources.

| Planned output | Contents |
| --- | --- |
| `archive-files.jsonl` | Original SAH ordinals/paths, offsets, lengths, versions, content hashes |
| `extraction-report.json` | Declared/read/extracted counts, errors, duplicates, distributions, integrity |
| `items.jsonl` | Original `(type,typeId)` and relationships |
| `skills.jsonl` | Skill/level/buff definitions and links |
| `mobs.jsonl` / `npcs.jsonl` | Entities, assets, and available client data |
| `quests.jsonl` | Stages, text, requirements, displayed rewards |
| `maps.jsonl` | Maps and included region/portal/position/asset relationships |
| `assets.jsonl` | Models, textures, animations, audio, effects, UI, fonts |
| `strings.jsonl` | Original text, encoding/language, IDs, usages |

Add catalogs as new systems are discovered. Do not create empty placeholders
to imply completed extraction. Each normalized record must reference its raw
record, manifest, schema, and evidence under `../schemas/provenance.schema.json`.
Preserve original numbers/units/missing values/unknown fields. Do not fill
missing values with EP8 defaults. Distinguish raw and derived values.

Structured records must be deterministic and schema-versioned. Large JSONL
exports may stay in cache with versioned counts/hashes/paths and reproduction
instructions. Report broken references, duplicate IDs, missing assets, and
assets without entity links. English metadata must not alter original client text.
