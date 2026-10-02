# WLD structures from the identified client

Specification: `EP45-A3-WLD-001`. Status: `decoded` for structure,
`unknown` for remaining field semantics and runtime behavior.
Executable SHA-256:
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Observation date: 2026-10-02. [Evidence windows](../analysis/wld-loaders.json)
bind the source bytes, PE addresses, disassembler version, and reproduction
arguments. [Catalog index](../catalogs/wld-catalogs.json) binds archive entry
IDs, source/output hashes, counts, offsets, tool version, and dependencies.

The reader is [wld.py](../../../tools/ep45-client/wld.py), version 1.0.0.
[Commands](../../../tools/ep45-client/README.md) reproduce the evidence and
exports without a server, database, SDK, or network connection.

## Storage and ordering

The observed files have no enclosing compression/encryption: their bytes
directly match the executable's sequential reads. Integer counts are signed
little-endian 32-bit values. Numeric record cells are exported as little-endian
unsigned 32-bit **storage bits**, preserving signed and floating-point
interpretations without imposing either. Nonfinite float bit patterns remain
integers; no JSON NaN conversion occurs. Units, axes, enum meanings, and most
signedness remain unknown.

`T256` and `T248` below mean fixed byte arrays used as text fields. Preserve
the entire array, including all bytes after the first NUL. ASCII text is
decoded; other UTF-8-decodable text is only a candidate. Unknown encoding and
language remain explicit. A missing NUL is recorded rather than silently
added. `U(n)` means an ordered block of `n` 32-bit storage cells, not a claim
that the cells are unsigned gameplay integers.

`A(layout)` means `i32 count` followed by exactly that many records.
All counts must be nonnegative and fit the remaining source bytes. Section
labels organize discovery; labels such as portals/NPCs/named areas do not
complete semantic validation of every field or prove a server rule.

| Order | Section | Serialized layout | Evidence |
| --- | --- | --- | --- |
| 1 | Signature | `DUN\0` or `FLD\0`, four bytes | Main loader `0x451db0`; comparisons `0x451eb1`, `0x451f14` |
| 2, FLD only | Extent and grids | `i32 extent`; `((extent / 2) + 1)^2` cells of two bytes, then the same number of one-byte cells | Grid reads `0x5a1b0a`, `0x5a1b29`; allocation `0x5a1b90`; byte extents reconcile for all 31 FLDs |
| 3, FLD only | Terrain materials | `A(T256 + U(1) + T256)` | `0x5a155c`, `0x5a15f0`, `0x5a161f` |
| 4 | Inner resource | `T256` | DUN read `0x451f40`; FLD read `0x452323` |
| 5–11 | Building, shape, tree, grass, vani0, vani1, dungeon | For each: `A(T256)` then `A(U(10))` | Calls `0x452384`–`0x45245e`; helpers `0x446890`, `0x446c80`, `0x447070` |
| 12 | Mani | `A(T256)` then `A(U(11))`, **44 bytes** per placement | Call `0x452477`; reads `0x41faae`–`0x41fae6` |
| 13 | Effect resource and records | `T256` then `A(U(10))` | `0x452480`; count `0x452506`; record reads `0x45252b`–`0x452573` |
| 14 | Object0 | `A(T256)`, `A(U(19))`, then `A(U(19) + U(19))` | `0x525ba0`; first list count `0x525c98`; pair count `0x525ee9`; pair loop `0x525f15`–`0x526390` |
| 15 | Object1 | `A(T256)` then `A(U(10))` | `0x5264d0`; call `0x452601` |
| 16 | Music | `A(T256)` then `A(U(9))` | `0x52c250`; reads `0x52c309`–`0x52c330` |
| 17 | Background sound | `A(T256)`; zone count; each zone has `U(6) + A(U(1))`; then `A(U(5))` spots | Reads `0x52c376`–`0x52c503` |
| 18 | Unknown regions | `A(U(7))`, **28 bytes** per record | Count `0x527c94`; reads `0x527d00`, `0x527d0d` |
| 19 | Portal candidates | `A(U(7) + T256 + T248 + U(6))`, **556 bytes** per record | `0x527f6a`; field reads `0x527fad`–`0x52803d` |
| 20 | Region groups | Group count; each group is `A(U(9))`, **36 bytes** per child | `0x5283b5`, `0x5283e1`, `0x52843d`–`0x528470` |
| 21 | Named-area candidates | `A(U(7) + T256 + T256 + U(2))`, **548 bytes** | `0x5286a2`; reads `0x5286d7`–`0x528727` |
| 22 | NPC candidates and associated points | Aggregate count; parent `U(6)`, point count, then `U(3)` per point | `0x528a8c`; reads `0x528acc`–`0x528bb0`; aggregate subtraction `0x528bd3` |
| 23, FLD only | Sky, cloud0, cloud1 resources | Three `T256` fields | `0x452640`–`0x45267d` |
| 24 | Trailer | `U(11)`, **44 bytes** | Three 12-byte reads and two four-byte reads in main loader |

The grid formula is consistent with all observed extents (1024 and 2048).
The allocation uses a global scale and an addition of 1; its initialization
and numeric terrain interpretation need further tracing. Synthetic tests use
smaller even extents to exercise bounds; they are not additional client samples.
Grid blocks are extracted with hashes and extents, but their terrain/collision
semantics are **not decoded**. The main loader also has a map-number-70 special
case setting an in-memory extent to 1600. The serialized file still has extent
2048; applying that override to extraction would misalign the source.

The NPC aggregate equals **parent count plus associated point count**.
The client subtracts point counts while iterating parents. Preserve the original
aggregate and separate counts. The relationship's purpose, NPC keys, and
point units remain unknown. Region groups are not a flat spawn array, and this
format does not establish mob spawn schedules, respawn, or loot.

Object0 has no nonempty lists in this archive. Its 76-byte records and 152-byte
pairs have static loader evidence and synthetic bounds tests, but no nonempty
source fixture or runtime validation. Do not label those variants as validated
against an extracted nonempty sample.

## Field dictionary and references

Each raw `parts` entry has `section`, `kind`, `offset`, and `size_bytes`.
Count/scalar entries retain `<i` and their original value. Numeric blocks retain
`offset`, `layout`, and ordered `values`; field index `j` has the label
`unknown_{4*j:03d}_u32_bits`, offset `block.offset + 4*j`, width four, unit
`unknown`, enum `unknown`, and semantic status `unknown`. Multiple blocks are
distinguished by their zero-based block index. `numeric_extremes` reports
storage-bit minima/maxima, not physical coordinate ranges.

Text entries retain exact `raw_hex`, offset/extent, `text`, `encoding_status`,
language, NUL presence, and nonzero padding count. Grid/signature entries
reference relative blob paths and hashes. Blob loading rejects traversal,
hash mismatch, missing bytes, gaps, or overlaps during reconstruction.

Normalized IDs are `<archive-entry-id>:<section>:<ordinal>`. These identify
evidence records; they **do not replace original client IDs**. `client_id` is
null until lookup semantics are proven. Numeric filename stems and the
`%d.wld` formatter at `0x4529ad` support investigation of map lookup; tracing
the caller's input and WorldMap.cfg linkage remains pending.

Placement/name index links remain `inferred`. Common groups use cell zero as
an index candidate, with `0xffffffff` recorded as a sentinel candidate. Mani
uses the second cell for its own name list: the first cell goes through a
different object at `0x41fb03` and must not be joined to the same list.
All raw indices and unresolved targets remain in the normalized catalog.

Resource filename links match original text inside roots passed by the main
loader: `entity/building`, `shape`, `tree`, `grass`, `vani`, `mani`, `object`,
and `world/dungeon`. Root evidence does not prove successful runtime loading.
Audio searches `Sound/music` and `Sound/back` as candidate roots. Every matched
archive entry ID is retained, including duplicate paths and case collisions.
Empty names and missing candidates are recorded as unresolved, not omitted.
Other resource fields remain extracted but unlinked.

## Export and validation contract

The raw JSON plus its binary blobs reconstructs the complete source file.
The normalized [record schema](wld-record.schema.json) describes catalog rows.
Bulk JSON/JSONL and grid blobs stay in cache with versioned counts/hashes.
Only indexes, schemas, tools, and small client-derived fixtures are versioned.
Original client text/filenames are never translated.

All 86 sources must pass size/hash verification, bounded parsing, complete
consumption, structured reconstruction, saved-export reconstruction, and a
second parse with matching counts. Failures stay in the source denominator
and cause exit status 1. Repeated runs verify existing exports instead of
overwriting them. New tool layouts require a new output directory.
See [validation and unresolved requirements](../validation/phase-a3-wld.md).
