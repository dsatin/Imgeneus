# Social and PvP: initial table evidence

Specification: `EP45-A2-TABLE-001`; baseline `rebirth-evolution-ep45-98c7dd3a`.
`Character/KillStatus.SData` (`tree-000012`) is structurally `decoded`.
[Structure](../schemas/sdata-tables.md), [source/export hashes](../catalogs/table-structures.json).

The 1,504-byte plain source contains a four-byte count of 60 and 60 fixed
25-byte records. The candidate shape is `(byte,int32,int16)` followed by six
`(byte,int16)` pairs. Candidate loading routine `0x478ca0` is called at
`0x424c62` with `KillStatus.SData`. Semantic interpretations from Parsec,
including faction/blessing/bonus names, remain unconfirmed in this sample.

Cache exports: `catalogs/structures-v1/kill-status.raw.jsonl` and `catalogs/structures-v1/kill-status.jsonl`.
Record ordinals are provenance, not confirmed server IDs. All bytes survive
structured round trip. Social/PvP actions, ranks, blessing effects, limits,
UI states, and packet layouts still require analysis. No authoritative combat
or faction policy has been implemented from this table.
