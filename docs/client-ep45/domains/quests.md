# Quests

## Identification and coverage

Specification ID: `EP45-A2-QUESTS-001`. Baseline/hash:
[baseline](../baseline.md). Source: `Npc/NpcQuest.Sdata`, quest section at
count offset 762,629. Complete records: 2,109, structurally `decoded`;
semantic status: `unknown`. Catalog/source hashes, tool 1.0.0, and command:
[report](../catalogs/extended-table-structures.json), [reproduction](../../../tools/ep45-client/README.md).

## Format and fields

Two-byte initial value, two texts, 87 numeric bytes, three 26-byte result
blocks, seven texts. All fields and offsets remain in the
[dictionary](../schemas/extended-table-layouts.json) and
[schema](../schemas/extended-sdata-tables.md). The loader changes the second
two-byte tail field from 60 to 70 under that exact condition; exports preserve
the raw value and make no claim about its meaning.

## Entities, assets, and relationships

The initial two-byte value is an ID candidate, not a confirmed lookup key.
NPC lists, matrix indices, item/mob/skill references, stages, requirements,
tracking flags, and reward semantics remain unresolved. Preserve duplicate
values and record positions until their relationships are established.

## UI and protocol

Quest dialogue, tracking, acceptance/cancellation, progress, completion, and
reward selection need controlled UI/protocol observations and static field
analysis. Three stored result blocks do not establish server reward policy.

## Validation

All 2,109 records consume the payload through offset 3,604,234 and reconstruct
identical bytes. Nested-format tests cover trailing text order and truncation.
`0x47aa35` calls reader `0x479500`; its initial storage reads and conditional
transform are recorded. Full reader semantics and runtime flows remain pending.

## Gaps and backend requirements

Confirm original IDs, enums, encoding, objective/reward fields, and cross-
references before import. Derive acceptance criteria from documented client
actions; isolate future authoritative policies from extracted client data.
