# Resource metadata and map structures

Specification IDs: `EP45-A3-RESOURCE-001`, `EP45-A3-ZON-001`.
Baseline executable hash:
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Observation date: 2026-10-01. [Catalog index/source hashes](../catalogs/resource-catalogs.json),
[reader and reproduction](../../../tools/ep45-client/README.md).

## Resource records

One JSONL row per original SAH entry, including duplicates and supplemental
entries. Retain its original stable ID, path, content SHA-256, size, SAF
offset, extension, baseline, and path-based domain hint. `status: inventoried`
is deliberately separate from `header_status` and integrity status. Path
hints and extension-based identifications remain `inferred`.

Every extracted file is rechecked against its original size/content hash.
Errors retain an entry and report outcome. Unimplemented signatures preserve
prefix bytes and an explicit reason; no file disappears from the denominator.
Media pixel/audio payloads remain undecoded, even when metadata is readable.

| Structure | Decoded metadata | Preserved unknown storage |
| --- | --- | --- |
| DDS signature | 124-byte header extent, dimensions, pixel-format extent, FourCC, raw mipmap count | Entire 128-byte header, body via original file/span/hash |
| BMP signature | DIB extent, width, raw signed height, bits per pixel | 54-byte header; body and additional header data remain in source |
| Candidate TGA | 18-byte bounded header, type, dimensions, depth, descriptor | Whole header; ID/palette/image payload remains unknown |
| RIFF/WAVE | Chunk extents/order, all fmt bytes, tag/channels/rate/alignment/depth, total data bytes | Unknown fmt extension, original chunk spans, audio/other chunks in source |
| WLD | `FLD\0`/`DUN\0` signature, FLD first int32 | Entire body remains opaque; terrain/collision/positions not decoded |

DDS/BMP detection takes precedence over filename extensions. Ten `.dds`
entries contain BMP signatures. TGA lacks a unique signature here, so its
header identification remains a candidate. Header decoding does not establish
entity links or visible behavior. Offset/count metadata is structural evidence,
not an inferred gameplay rule.

Two audio sources omit alignment padding after odd-sized data chunks:
`Sound/back/bg_mzone003.wav` and `bg_mzone004.wav`. The strict padded walk fails;
an explicitly labeled unpadded walk consumes each complete file. Preserve the
standard-layout failure in the catalog, all chunk offsets, and a source-anomaly
entry. Do not repair these sources or claim runtime playback was verified.

## TacticsZone.zon

The source is `world/TacticsZone.zon`, `tree-022506`, 3,428 bytes. Format tag
5 and count 35 occupy two little-endian int32 values. Each record has three
bytes, fourteen four-byte values, one two-byte value, and one int32 byte-counted
text. Numeric block length: 61. The first record starts at 8, length 154;
the last starts at 3,328, length 100. Exact reconstruction consumes all bytes.

Use raw unsigned integer bits for float candidates, preserving NaNs and signed
zero. Do not label axes, world units, map IDs, permissions, or region semantics
without client field-use evidence. Every raw text and terminator count survives.
Only format tag 5 is supported; other tags fail explicitly. Parsec's ZON reader
was infrastructure for probing this layout; bytes from this sample establish
structural decoding, while a dedicated executable loader remains pending.

## WorldMap.cfg

Source `tree-000008`, 2,976 bytes. Preserve each line's exact bytes, newline,
offset and ordinal. Recognize ASCII sections/keys, retain duplicate sections
and fields, and keep unknown/comment lines. Normalize decimal integer
candidates separately from raw values: `0208` becomes candidate 208 while
the original four bytes remain unchanged. Whole-file reconstruction is exact.

There are 20 sections: `WorldMap` with literal `count=19`, plus 19 numbered
sections. Keys include original `Country`, `MapNum`, `Click_*`, and `ImgPos_*`.
Their names are source evidence, not proof of coordinate units or permissions.
MapNum-to-WLD filename matches are only candidate relationships and preserve
all target entries, not a dictionary that drops duplicate names.

## Coverage limits

These catalogs start A3 and identify resource structure, references, and
outstanding readers. Model/skeleton/animation/effect formats, WLD contents,
character/mob/NPC resource links, UI states/actions, packet layouts, and runtime
coverage remain pending. A2 stays open with its explicit gaps; Phase B is gated
by A7.
