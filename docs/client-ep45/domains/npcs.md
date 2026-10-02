# NPCs and dialogue

## Identification and coverage

Specification ID: `EP45-A2-NPCS-001`. Baseline/hash:
[baseline](../baseline.md). `Npc/NpcQuest.Sdata` yields 1,510 NPC records
in 13 groups; `Npc/PriestTalk.SData` yields 86 records in four sections.
Status: structurally `decoded`, semantics `unknown`.
Source/decoded hashes, cache catalogs, tool 1.0.0, and reproduction:
[report](../catalogs/extended-table-structures.json), [commands](../../../tools/ep45-client/README.md).

## Format and fields

See [extended schema](../schemas/extended-sdata-tables.md) and
[field dictionary](../schemas/extended-table-layouts.json). Preserve numeric
headers, two texts, both two-byte lists, group-zero byte pairs, and all
three group-one targets. Possible coordinate values are preserved as raw
four-byte bits. PriestTalk has one byte and two texts per record; all 172
texts have unresolved encodings. No dialogue text is translated in place.

## Entities, assets, and relationships

Original numeric values, section ordinals, and list entries are preserved.
The two-byte header field is an ID candidate; `client_id` remains null until
client lookup semantics are proven. The 65,536-cell matrix is fully accounted
for but its index meanings remain unknown. Type/faction, model, shops,
destinations, quest links, and map positions require field/resource evidence.
No spawn positions or shop rules have been invented.

The [WLD catalog](../catalogs/wld-catalogs.json) adds 2,707 NPC candidate parents
with 779 associated points. Their original aggregate is 3,486, not the parent
count. Fields/offsets remain raw; links to NpcQuest IDs, point semantics,
appearance, and service behavior are unresolved. See [WLD schema](../schemas/wld.md).

## UI and protocol

Dialogue, merchant, and gatekeeper are candidate interpretations of these
variants, not validated screens/actions. PriestTalk runtime usage has no
identified dedicated loader. NPC interaction packets are pending.

## Validation

Complete payload consumption, byte reconstruction, nested count bounds,
repeated entries, matrix dimensions, and target bit patterns pass checks.
`0x47a050` provides partial loader corroboration; full field-use analysis is
pending. No NPC interaction was newly validated at runtime.

## Gaps and backend requirements

Prove lookup IDs and list/matrix relations, character encoding, resource
links, target units, and service behavior before importing definitions.
Decoded NPC definitions are not authoritative spawns or server policies.
