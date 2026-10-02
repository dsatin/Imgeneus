# Extended SData structures

Specification ID: `EP45-A2-EXTENDED-001`. Baseline:
`rebirth-evolution-ep45-98c7dd3a`; executable SHA-256
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Observation date: 2026-10-01. [Source hashes and exports](../catalogs/extended-table-structures.json),
[field dictionary](extended-table-layouts.json), [record schema](extended-table-record.schema.json),
[executable evidence](../analysis/extended-table-loaders.json),
[commands](../../../tools/ep45-client/README.md).

All offsets address decrypted payloads. Counts and text byte lengths occupy
little-endian int32 storage; negative and out-of-bounds lengths are rejected.
Texts retain exact bytes, terminators, and encoding status. Non-UTF-8 text
remains null with raw hex; no replacement or in-place translation is performed.
Numeric storage types describe byte widths, not confirmed semantic types.
The field dictionary assigns `unknown_<offset>` names within each block.
Record offsets and nested block offsets distinguish repeated field names.

## Skill and NpcSkill

The shared loader at VA `0x461a70` reads a four-byte group header (the loaded
group count uses its low 16 bits), then nine records per group. The analyzed
sources have zero upper header bits. Each record contains two length-prefixed
texts followed by 116 numeric bytes. The dictionary includes all 84 numeric
reads, tied to individual instructions in the executable evidence. Runtime
object stride `0x88` is not the serialized record size.

| Entry | Declared groups | Expected records | Complete records | Source outcome |
| --- | --- | --- | --- | --- |
| `tree-000013`, `Character/Skill.SData` | 374 | 3,366 | 3,360 | `unknown`: six terminal records missing |
| `tree-015695`, `Monster/NpcSkill.SData` | 384 | 3,456 | 3,456 | `decoded` |
| `supplemental-000002`, `Skill.SData` | 374 | 3,366 | 3,366 | `decoded`; active usage unknown |

The active Skill payload ends exactly after slot ordinal 2 of group ordinal
373, at offset 612,062. CRC32 and cipher round trip already passed. This is
a mismatch between source contents and the static nine-slot expectation,
not an extraction checksum failure. The reader exports complete records,
records the six-record discrepancy, and returns a failing validation exit
code. Truncation inside a record remains a hard parsing error. The supplemental
source is separate evidence and never replaces the active source.

Group/slot ordinals are provenance, not invented skill IDs or confirmed levels.
The later [lookup audit](../validation/a2-pending.md) proves one-based group/slot
address selection; its enriched catalogs use a separate schema and do not
claim packet-ID semantics or modify the original structural exports.
Numeric offset 22 is reduced modulo 1,000 by the client loader; exports retain
the original value. Meaning, units, buff/effect semantics, and lookup IDs are
unresolved. A possible runtime out-of-bounds read is a hypothesis requiring
debugging; no crash or effect of the missing records has been demonstrated.

## PriestTalk

`tree-019145`, `Npc/PriestTalk.SData`, contains four sections with counts
25, 19, 21, and 21, at offsets 0, 14,377, 25,617, and 38,287. Each record is
one byte followed by two length-prefixed texts. All 50,985 bytes are consumed
and reconstructed. All 172 texts have unresolved encodings; byte patterns
suggest Korean legacy encoding, but no client conversion routine proves it.
The section/byte meanings and runtime usage remain unknown. This structure
is decoded from source bytes; a dedicated executable loader is still pending.

## NpcQuest

`tree-019146`, `Npc/NpcQuest.Sdata`, contains 13 count-prefixed NPC groups,
a fixed 65,536-cell matrix with two count-prefixed two-byte arrays per cell,
and a count-prefixed quest section. A Parsec layout was used as a probe;
full source consumption and lossless reconstruction verify the candidate
structure on this sample. The loader at `0x47a050`, its two nested `0x100`
matrix bounds, and its call at `0x47aa35` to reader `0x479500` provide partial
static corroboration. Complete field-use confirmation is pending.

NPC group counts are `[313,72,52,2,8,40,747,150,24,83,6,11,2]`, totaling
1,510 records. Every NPC has a numeric header, two texts, and two
count-prefixed two-byte lists. Group zero adds a byte after the first
two-byte field and a count-prefixed array of byte pairs after the texts.
Group one adds three targets, each with a two-byte value, three four-byte
values, one text, and a trailing four-byte value. The three values are
possible coordinates, stored as original bits to preserve NaNs and signed
zero without asserting coordinate semantics.

The matrix starts at 235,973, occupies 526,656 bytes, and contains 637
nonempty arrays out of 131,072. The sparse export lists those arrays with
original cell/list ordinals and offsets. Empty arrays are accounted for by
the fixed matrix dimensions and reconstructed as zero counts; the entire
matrix's hash and source span are recorded. Sparse rows are not entity counts.
Matrix index meanings and relationships remain unknown.

The quest count is 2,109 at offset 762,629. Each record contains a two-byte
value, two texts, 87 numeric bytes, three 26-byte result blocks, and seven
more texts. The payload ends exactly at 3,604,234. The client changes the
second two-byte value in the 87-byte block from 60 to 70 when loading it
(`0x4796da`/`0x4796e0`); raw exports do not apply this transformation.
Neither a semantic label nor an original server rule follows from that use.

## Exports and limits

Raw and normalized JSONL preserve numeric block boundaries, nested lists,
text bytes, source spans, and original values. Normalized IDs combine entry,
domain, group, and record ordinals; `client_id` is null until lookup semantics
are proven. JSONL is authoritative; no lossy CSV export is produced.

Sources with missing records remain in the report denominator. Exported
complete records can be `decoded` while their enclosing source remains
`unknown`; they do not demonstrate complete source validity. Existing exports
are hash-verified without replacement. All field meanings, references, enums,
assets, runtime effects, and server policies need further evidence.
