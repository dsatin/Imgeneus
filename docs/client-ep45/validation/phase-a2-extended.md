# A2 extended structural decoding

Evidence ID: `EP45-A2-VALIDATION-002`. Observation date: 2026-10-01.
Baseline and executable hash: [baseline](../baseline.md).
Project before this task: `0f68fb8b1011f0edf79642b2b53670db8559da26`.
Parsec probe source: `ebac92c473175a5c0aae29c1e370a2a299d1dedc`.
Tool: `extended_tables.py` 1.0.0; exact tool/dependency hashes, parameters,
source hashes, counts, cache paths, export hashes, and first/last records:
[machine-readable report](../catalogs/extended-table-structures.json).
See [schema](../schemas/extended-sdata-tables.md) and
[loader windows](../analysis/extended-table-loaders.json).

## Results

| Coverage measure | Result |
| --- | --- |
| New active sources examined | 4/4 remaining SData sources |
| New active sources fully structurally decoded | 3/4 |
| Active source with a count discrepancy | 1/4: Skill, six missing terminal records |
| New complete records from fully decoded active sources | 7,161: 3,456 NpcSkill + 86 PriestTalk + 1,510 NPCs + 2,109 quests |
| Complete records recovered from inconsistent active Skill | 3,360/3,366 expected |
| Supplemental records decoded separately | 3,366 Skill; runtime usage unknown |
| Nonempty matrix arrays | 637/131,072; not entity records |
| Fully structurally decoded active SData sources, cumulative | 8/9 |
| Complete records in fully decoded active SData sources, cumulative | 27,198 |
| Complete records including recovery from active Skill, cumulative | 30,558 |
| Semantically validated formats | 0 |
| Newly validated runtime interactions | 0 |

The active Skill payload passes container integrity but contains 3,360
records while the executable's nine-slot layout and 374-group header require
3,366. The separate supplemental source has 3,366. Neither active usage of
the supplemental source nor a causal connection to a gameplay fault has
been established. The discrepancy remains blocking evidence work.

All five examined payloads have exact byte consumption and lossless
structured read/write reconstruction, including the inconsistent Skill
header. Reconstruction alone does not resolve a count mismatch. The CLI
deliberately exits **1** and records `missing-terminal-records`; this is an
expected validation failure for this sample. Other parse/output failures
also produce explicit report errors rather than disappearing from coverage.

49 automated tests passed, covering the previous extraction/cipher readers
and 12 new nested-format tests. New cases include missing terminal slots,
truncation inside records, extra bytes, invalid counts/text lengths, all four
PriestTalk sections, NPC variants, repeated values, raw signaling-NaN and
signed-zero bit patterns, fixed matrix dimensions, and trailing quest texts.
The [small fixture](../../../tools/ep45-client/fixtures/skill-records.json)
preserves the first/last NpcSkill source spans, raw bytes, hashes, and expected
storage values; it works without the installed client. Its test wraps each
original record in an artificial one-group header and expects eight missing
slots, explicitly distinguishing test framing from original source data.
The second catalog run verifies existing exports without replacement.

## Outstanding work

Confirm field semantics, signedness, units, enums, original lookup IDs,
encoding conversion, references, and asset links. Resolve active Skill's
missing records through executable/runtime evidence without editing source
data. Confirm the full NpcQuest reader and PriestTalk runtime usage, then
analyze supplemental usage and backend-relevant WLD/ZON/resource formats.
Phase A remains active; this report does not release Phase B.
