# Skills and buffs

## Identification and coverage

Specification ID: `EP45-A2-SKILLS-001`. Baseline/hash: see
[extended schema](../schemas/extended-sdata-tables.md) and [baseline](../baseline.md).
Sources: `Character/Skill.SData`, `Monster/NpcSkill.SData`, and separate
supplemental `Skill.SData`. Active complete records: 3,360 and 3,456;
the first source lacks six expected slots and remains `unknown`.
Supplemental complete records: 3,366, with active usage unknown.
Catalogs, hashes, tools, and commands: [report](../catalogs/extended-table-structures.json),
[`extended_tables.py` 1.0.0](../../../tools/ep45-client/README.md).

## Format and fields

Two length-prefixed texts and a 116-byte tail per record, nine slots per
declared group. All 84 tail fields retain original storage and unknown
meanings in the [dictionary](../schemas/extended-table-layouts.json).
Text encodings are ASCII/UTF-8 candidates; no encoding conversion is confirmed.
Numeric offset 22 has a documented modulo-1,000 loading transformation;
exports retain original bytes/values.

## Entities, assets, and relationships

Group/slot ordinals identify provenance, not confirmed skill/level IDs.
The [A2 audit](../validation/a2-pending.md) subsequently confirms one-based
group/slot address keys at `0x462350`, exported separately as static lookup
keys. The first tail byte is not that positional key; on-wire IDs remain pending.
No IDs are renumbered or synthesized as original client IDs. Class, icons,
animation/effects, targets, costs, duration, range, and buff links remain
unknown until individual field uses and resource references are traced.

## UI and protocol

Skill panels, buff display, quickbar actions, and corresponding packet fields
remain uncorrelated. Decoded records do not establish packet layouts.

## Validation

Source hashes, container CRC/cipher verification, full structured byte
reconstruction, first/last records, and bounds tests are recorded. Shared
loader `0x461a70` confirms the tail and nine slots. Runtime validation: zero
new skill actions. The active count mismatch is explicitly retained.

## Gaps and backend requirements

Resolve missing slots and prove lookup semantics before import or gameplay
implementation. Keep active/supplemental tables distinct. Server-only costs,
formulas, and validation policies cannot be attributed to the original
server without client evidence. Phase B depends on these remaining contracts.
