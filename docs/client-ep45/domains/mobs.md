# Mobs

Specification: `EP45-A2-TABLE-001`; baseline `rebirth-evolution-ep45-98c7dd3a`.
Status: `decoded` structurally; semantic status: `unknown`.
Source: active `Monster/Monster.SData`, archive entry `tree-015696`.
[Structure](../schemas/sdata-tables.md), [report](../catalogs/table-structures.json).

3,001 records parse completely: a four-byte declared count, then a byte-counted
text and 31 numeric bytes per record. The client routine at `0x4615a0`, called
at `0x424c7e` with `Monster.SData`, demonstrates corresponding string and numeric
copies in the `0x461810`–`0x46194a` window.

No explicit mob ID occurs in this candidate structure. Original ordinals and
source offsets remain provenance identifiers. The
[A2 audit](../validation/a2-pending.md) confirms zero-based uint16 lookup
at `0x461990`; packet IDs and other field meanings remain uncorrelated.
The normalized catalog uses `unknown_*` fields, without treating infrastructure
names such as HP/AI as confirmed semantics. ASCII/UTF-8 text candidates retain
all original bytes. Structured round trip is identical for the whole file.

Cache exports: `catalogs/structures-v1/mobs.raw.jsonl`, `catalogs/structures-v1/mobs.jsonl`, indexed by
report hashes. Model/animation/audio links, map placements, gameplay behavior,
and packet/UI interactions remain pending. Spawns, respawn, drops, and server
formulas cannot be inferred from these records alone.
