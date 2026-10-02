# Dungeon and water structures

Specification: `EP45-A3-SPATIAL-001` (variants `DG` and `WTR`). Observation:
2026-10-02. All findings apply exclusively to executable SHA-256
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`
and source hashes in the [catalog index](../catalogs/spatial-catalogs.json).
The [loader profile](../analysis/spatial-loaders.json) records 12 bounded
disassembly windows, four exact strings, PE mappings, byte hashes, commands,
and tool versions. [Reproduction](../../../tools/ep45-client/README.md)
requires no server, database, SDK, or network.

`spatial.py` 1.0.0 derives read boundaries from this executable. Parsec's WTR
reader was a comparison candidate; it was not accepted as episode evidence.
All numeric words below are preserved as unsigned storage bits. Possible
floating-point, color, timing, bounds, and coordinate meanings remain unknown
unless separately corroborated. No field is discarded to make parsing succeed.
These are structural specifications, not completed gameplay semantics.

## WTR: water parameters and texture list

No signature, encryption, or compression was observed in the three identified
sources. Their verified structure is little-endian and has this exact order:

| Field | Offset/width | Representation | Client read/use |
| --- | --- | --- | --- |
| `unknown_000_u32_bits` | 0 / 4 | Raw word; float32 views 128, 64, 64 | Read VA `0x59efeb`; passed to `0x59ed40`, which writes vertex-buffer components |
| `unknown_004_u32_bits` | 4 / 4 | Raw words `0xbfffffff`, `0xd8ffffff`, `0x98ffffff` | Read VA `0x59f004`; passed to `0x59edb0`, which writes vertex-buffer words |
| `unknown_008_u32_bits` | 8 / 4 | Raw words 40, 150, 40 | Read VA `0x59f01d`; stored at object offset `0x24`; time/unit semantics pending |
| `texture_count` | 12 / 4 | Nonnegative little-endian i32 | Read VA `0x59f02c`; controls the fixed-text loop |
| `texture_names[i]` | `16 + 256*i` / 256 | Exact bytes, first-NUL text view, retained padding | Read VA `0x59f09e`; loader call `0x59e790` at `0x59f0d5` |

The float32 view is a reversible storage interpretation, not a proven height
unit. The three files contain 30, 32, and 32 texture names; `16 + 256*count`
equals each complete source size. Nonzero bytes after NUL are retained.
ASCII texts are identified as ASCII; other UTF-8 decodes remain candidates,
and undecodable bytes retain `text: null`. Language is unknown.

The WLD FLD branch reads a 256-byte water name and invokes `0x59ef20` with
`data/entity/water`. Texture names use that same root. All 98 nonempty water
texture names have same-stem DDS candidates, but none has an exact extension
match. Extension replacement or successful rendering has not been validated.

## DG: external textures and an eight-child spatial tree

No magic, cipher, or compressed body was observed in the 47 verified `.dg`
sources. The DUN WLD branch invokes `0x5942c0` with `data/world/dungeon`.
The serialized order is:

| Field | Width/order | Client evidence |
| --- | --- | --- |
| File header | Six u32 storage words, 24 bytes | Read VA `0x59438b`; passed to `0x526cf0` |
| Texture count/list | i32 count, then `count * 256` exact text bytes | Reads `0x5943e7`, `0x594427`; root string at VA `0x6f8680`: `data\entity\texture` |
| External page count | i32, four bytes | Read `0x5944c6`; `0x591f60` requests DDS files without consuming DG body bytes |
| Root-present flag | u32, four bytes | Read `0x59452b`; any nonzero value invokes `0x593f80` |
| Root node | Present only when the flag is nonzero | Node layout below; recursive depth-first serialized order |

The page helper uses `%s\%s_L%d.%s` at VA `0x6bc9b0`, a zero-based ordinal,
and default `dds`. For a `.dg` filename it removes the final three extension
characters, producing a candidate such as
`world/dungeon/DUN_LOGIN/DUN_LOGIN_L0.dds`. Page counts are external-resource
counts, not embedded record or byte counts. Runtime selection of alternate
extensions is not covered. Filename generation for `.dg_pv` is unverified.

### Node layout

| Field | Width/order | Read VA |
| --- | --- | --- |
| Header block 0 | Three u32 storage words, 12 bytes | `0x593fb1` |
| Header block 1 | Six u32 storage words, 24 bytes | `0x593fc7` |
| Header block 2 | Six u32 storage words, 24 bytes | `0x593fe0` |
| Group count | Nonnegative i32 | `0x594000` |
| Groups | Repeated group structure | `0x5940e2` calls `0x593de0` |
| Auxiliary mesh | Flag and conditional arrays below | `0x594105` calls `0x593160` |
| Children | Exactly eight repetitions of u32 presence flag followed immediately by a node if nonzero | Flag read `0x59414e`, recursive call `0x5941a8`, loop bound eight at `0x5941b9` |

The three header blocks are exported together as 15 consecutive storage words;
the original 12/24/24 boundaries are documented here. Axes, units, octant
ordering, and spatial meanings remain unknown. `node_path` is an evidence
path such as `root/3/2`, preserving child slots, not a recovered gameplay ID.
There are 2,024 nodes, and the maximum observed depth is four. The tool depth
bound of 64 is a resource guard, not a client or gameplay limit.

### Group and render patch

A group starts with one u32 storage word (read `0x593e03`) and an i32 patch
count (read `0x593e28`). It then calls `0x593980` per patch. The first group
word is a texture-index candidate: all 22,889 values fall within their own
file's preserved texture list. This numerical association is `inferred`;
the file-local original values are not renumbered.

| Patch field | Width/order | Read VA |
| --- | --- | --- |
| Unknown word | Four u32 storage bytes | `0x593990` |
| Vertex count | Nonnegative i32 | `0x5939a7` |
| Vertices | If vertex count is positive: 44 bytes / 11 u32 storage words each | `0x593a02`; stride `0x2c` |
| Triangle count | i32, only if vertex count is positive | `0x593a17` |
| Triangles | Three little-endian u16 indices per triangle | `0x593a54`; count multiplied by six |

When vertex count is zero, the client skips **both** vertices and the triangle
count/array. Patch words, packed values, floats, texture coordinates, normals,
and material/page semantics are unresolved. Every vertex word is exported;
NaN payloads and signed-zero bits remain unchanged. All triangle indices are
checked against their local vertex count. Geometry instances are not mobs,
NPCs, or authoritative spawn records.

### Auxiliary mesh

`0x593160` first reads a u32 presence flag at `0x59317b`. Zero consumes no
further mesh fields. A nonzero flag reads an i32 vertex count at `0x593194`,
`count * 12` vertex bytes at `0x5931c1`, an i32 triangle count at `0x5931cf`,
and `count * 6` index bytes at `0x593211`. Vertices contain three preserved u32
storage words; triangles contain three u16 indices. There are 1,588 included
meshes, 165,187 vertices, and 158,045 triangles. Collision or gameplay use
has not been established; calling these authoritative collision meshes would
exceed the evidence.

## DG_PV outcomes

All 12 `.dg_pv` files share the initial six-word/count/fixed-text pattern,
but the verified DG reader rejects each further body with invalid counts.
Offsets/errors and source hashes remain in the index. No alternative stride,
padding, or field meaning was guessed to conceal these failures. A matching
loading routine, full structure, activation conditions, and runtime use remain
unknown. These files remain in the 62-source denominator.

## Export and field dictionary conventions

The [record schema](spatial-record.schema.json) covers the two decoded variants.
Raw JSON contains ordered `parts`, `counts`, source identity, and consumed
length. Normalized JSONL contains every part with stable entry/part evidence
IDs, baseline/hash/path/schema references, `client_id: null`, and status
`decoded` with `semantic_status: unknown`.

- Scalar/count: absolute source offset, extent, little-endian layout, raw value.
- Record: ordered numeric blocks and exact fixed-text bytes, each with offsets.
  An unnamed word at relative byte offset `n` is `unknown_n_u32_bits`.
- Array: offset, count, stride implied by `layout`, and all typed integer rows.
  Render vertices use `<IIIIIIIIIII`, auxiliary vertices `<III`, triangles
  `<HHH`. Cell offset is `array_offset + row*stride + column*word_width`.
- Node/group/patch context preserves tree paths and local ordinals. These are
  evidence/structure coordinates, not substituted original game IDs.
- Resource link: original source span and text, loader roots, exact target
  archive IDs, separately labeled same-stem DDS candidates, and unknown runtime
  status. Generated page links point to the count field and identify generation
  explicitly. Duplicate targets would be preserved.

`rebuild_spatial` validates contiguous parts/fields, array counts and extents,
and total length. Saved JSON reconstructs every source byte. Parsing that
reconstruction verifies read→write→read counts. Large numeric arrays stay in
cache JSON/JSONL rather than opaque skipped blobs. Small complete WTR sources
and two exact dungeon leaf spans provide offline fixtures; their synthetic
envelopes are explicitly separated from client evidence.

## Remaining contracts

Resolve DG_PV, texture extension lookup, ten missing generated page candidates,
node/vertex spatial semantics, auxiliary-mesh purpose, water parameters,
resource activation, and runtime behavior. Sky/cloud/effect/model dependencies
and entity-definition joins remain separate pending A3 work. These findings
do not release A7 or authorize gameplay semantics inferred from EP8.
