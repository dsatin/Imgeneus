# Economy: initial table evidence

Specification: `EP45-A2-TABLE-001`; baseline `rebirth-evolution-ep45-98c7dd3a`.
Cash and guild-house tables are structurally `decoded`; field meanings are
`unknown`. [Source hashes/counts](../catalogs/table-structures.json),
[structures](../schemas/sdata-tables.md).

Active `Cash.Sdata` contains 108 product-shaped records, each with four int32
values, 24 int32/byte pairs, and three byte-counted texts. Four text fields have
unresolved encodings. Cash loader candidate: `0x4623a0`, called at `0x424cb6`.
Two supplemental Cash sources remain separate and are not substitutions.

`Npc/GuildHouse.SData` has three header int32 values, 36 fixed 15-byte records,
and 24 trailing int32 values; the full 648 bytes round-trip identically.
Its executable filename reference is at `0x4c5ec1`. Confirm field meanings,
prices/currencies, NPC links, shop UI actions, and packets through client usage.

Exports in cache: `catalogs/structures-v1/cash*.jsonl` and `catalogs/structures-v1/guild-house*.jsonl`.
Their hashes are indexed in the report. These tables do not prove support or
absence of trade, bank, warehouse, mail, or auctions; those systems need
independent UI/protocol investigation.
