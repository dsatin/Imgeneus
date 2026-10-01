# Items

Specification: `EP45-A2-TABLE-001`; baseline `rebirth-evolution-ep45-98c7dd3a`.
Status: `decoded` structurally; semantic status: `unknown`.
Source: active `Item/Item.SData`, archive entry `tree-014671`.
[Structure and fields](../schemas/sdata-tables.md),
[hashes/counts/first-last records](../catalogs/table-structures.json).

16,832 records across 100 declared groups parse completely. Original candidate
`(type,typeId)` bytes are unique and match group numbers without renumbering.
Two length-prefixed texts precede 81 numeric bytes. Normalized fields retain
unknown names until their client uses are traced; requirement/stat/price names
from the EP5 infrastructure reader are not validated EP4.5 semantics.

Cache exports: `catalogs/structures-v1/items.raw.jsonl` and `catalogs/structures-v1/items.jsonl`, indexed
by hashes in the report. All item texts decode losslessly as ASCII/UTF-8
candidates. Every decoded byte survives structured round trip.

Client loading routine candidate: `0x460c80`, called with `item.SData` at
`0x42a3cc`. The bounded analysis window shows group counts, two byte-counted
strings, and numeric copies. Full field-use, icon/model links, slots/limits,
UI actions, and inventory packet relationships remain pending.

The backend may eventually import confirmed original IDs and fields. No
existing EP8 seed, rule, or serializer is validated by this structural export.
