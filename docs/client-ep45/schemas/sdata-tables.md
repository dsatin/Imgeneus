# Initial SData record structures

Specification ID: `EP45-A2-TABLE-001`. Source baseline:
`rebirth-evolution-ep45-98c7dd3a`. [Results and source hashes](../catalogs/table-structures.json),
[numeric field dictionary](sdata-table-layouts.json),
[normalized-record schema](table-record.schema.json),
[reproduction](../../../tools/ep45-client/README.md).

These are lossless structural readers, not completed semantic schemas.
Parsec at `ebac92c473175a5c0aae29c1e370a2a299d1dedc` supplied candidate layouts.
Actual client bytes establish counts and complete consumption; executable
loader windows provide additional evidence for items/mobs. No Parsec property
name is promoted to a confirmed client field merely because parsing succeeds.

## Observed structures

All counts/lengths use four-byte little-endian storage. Text lengths count
bytes, including the observed terminators; preserve raw bytes and terminator
counts. Signed interpretation of numeric storage is still a candidate.

| Source | Structure | Numeric bytes per record | Records |
| --- | --- | --- | --- |
| `Item/Item.SData` | Group count; per-group record count; two length-prefixed texts then numeric tail | 81 | 16,832 |
| `Monster/Monster.SData` | Count; one length-prefixed text then numeric tail | 31 | 3,001 |
| `Cash.Sdata` | Count; four int32 values, 24 `(int32,uint8)` pairs, three length-prefixed texts | 136 | 108 |
| `Character/KillStatus.SData` | Count; `(uint8,int32,int16)` and six `(uint8,int16)` pairs | 25 | 60 |
| `Npc/GuildHouse.SData` | Three int32 values; 36 fixed records; 24 trailing int32 values | 15 | 36 |

Guild-house fixed records are five bytes, four two-byte values, and two bytes.
The [JSON dictionary](sdata-table-layouts.json) specifies every numeric offset,
width, and candidate type. All unresolved meanings use `unknown_*` names.

The item file declares 100 groups. The first two tail bytes form unique
candidate `(type,typeId)` pairs, and the first byte matches the one-based group
number for all 16,832 records. Those original bytes are preserved without
renumbering. Full client lookup semantics still require analysis.
Mob records contain no explicit identifier in this layout; ordinal is a
provenance position, not a confirmed mob ID. Guild-house trailing values and
cash pair values remain raw references until target catalog links are proven.

## Export and validation

Each raw record preserves ordinal, decoded offset/length, original text bytes,
numeric layout/values, and item group positions. Normalized records add stable
provenance IDs, source/decoded hashes, schema ID, and unknown field names.
`client_id` remains null; item candidates are recorded separately as `inferred`.
Record/text offsets refer to decoded payload bytes, not encrypted SAF positions.
Numeric field names use stable offsets within the numeric block;
`numeric_block_offset` locates that block inside each variable-length record. Encrypted
sources link back to their archive interval through the container report.

Every reader checks bounded counts/lengths, consumes the entire source, and
rebuilds identical source bytes from parsed numbers and preserved text. First/
last record samples and all export hashes are versioned; bulk JSONL remains
in cache. Existing exports are verified without replacement.

ASCII text is lossless and unambiguous. Non-ASCII valid UTF-8 is only an encoding
candidate until client conversion is analyzed. Four cash text fields are not
valid UTF-8: retain their hex bytes and null text values instead of replacement
characters. No client evidence has been translated.

## Remaining work

The [extended schemas](extended-sdata-tables.md) now describe Skill, NpcSkill,
PriestTalk, and NpcQuest. Active Skill has six missing expected records;
the other three active sources are fully structurally decoded. Analyze item/mob
field uses and lookup semantics; confirm cash/guild-house/kill-status loaders,
encodings, enums, units, and references. Supplemental layouts need separate
usage evidence. WLD/ZON, assets, UI, protocol, and runtime coverage remain
separate phase A tasks. These readers do not release phase B.
