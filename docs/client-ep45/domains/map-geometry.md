# Dungeon geometry and water resources

## Identification and coverage

Specification `EP45-A3-SPATIAL-001`; observation date 2026-10-02. Baseline:
[identified client](../baseline.md), executable SHA-256
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Sources: 47 `.dg`, 12 `.dg_pv`, and three `.wtr` archive entries. All 62 files
were rechecked against extraction hashes. Fifty files across two structural
families decode completely; 12 DG_PV bodies remain unknown. Tools 1.0.0,
[commands](../../../tools/ep45-client/README.md),
[catalog/hash index](../catalogs/spatial-catalogs.json), and
[validation](../validation/phase-a3-spatial.md) reproduce the result.

## Format and fields

The [field dictionary and binary layouts](../schemas/spatial-resources.md)
and [record schema](../schemas/spatial-record.schema.json) cover water words,
fixed texture names, dungeon headers, nested groups/patches, eight child slots,
44-byte render vertices, 12-byte auxiliary vertices, and three-u16 triangles.
Raw numeric storage, unknown fields, source offsets, text padding, and all
mesh arrays remain intact in JSON/JSONL. No coordinate unit, collision rule,
water height unit, or physics meaning is assigned without further evidence.

## Entities, assets, and relationships

Cataloged structures: 2,024 tree nodes, 22,889 groups, 23,076 patches,
3,021,237 render vertices, and 1,411,815 render triangles. Auxiliary geometry:
1,588 included meshes, 165,187 vertices, and 158,045 triangles. Texture lists
contain 2,993 dungeon entries and 98 water entries, including nine empty dungeon
names. These are serialized structure counts, not unique gameplay entities.
Original game/entity IDs are unknown; entry/part/tree IDs identify evidence.

There are 86 WLD inner-resource links: 84 exact matches and two empty FLD
names. They target 41 distinct DG entries and all three WTR entries. Six DG
entries have no exact match in this particular WLD field; that does not prove
they are unused by other references or client routines. Dungeon placement
names were already cataloged in the WLD work.

All 22,889 group texture-index candidates fit their own file's texture list.
The 3,082 nonempty texture names have same-stem DDS candidates but no exact
extension matches. DDS replacement remains an unvalidated hypothesis, kept
separate from matched references. Of 375 generated DDS page links, 365 match;
ten do not, involving `Login_eternity_territory_01` and `test000_01`. Empty,
missing, and inferred relationships remain in the integrity denominator.

## UI and protocol

These resources are loaded by map routines. No new map navigation action,
water rendering/interaction, collision behavior, packet, or client acceptance
was exercised. Map entry/portal/session contracts remain separate A4–A6 work.
Static file loading is not evidence of authoritative movement or spawn rules.

## Validation

All 206,067,062 source bytes were size/hash verified; 145,803,996 bytes from
the 50 complete sources were structurally decoded. Every decoded source
consumes/reconstructs exactly; saved JSON→bytes→reader counts agree. Arrays
retain every numeric cell and index; no skipped opaque geometry blob remains
in these 50 sources. Repeated export generation verifies existing files.

Ninety tests pass across extraction tools. New tests cover all five small
source fixtures, truncation/count corruption, zero-vertex variants, raw NaN
bits, nested child slots/depth bounds, local index limits, export corruption,
output protection, resume, input integrity, and retained failure denominators.
The two dungeon fixtures contain exact leaf spans inside explicitly synthetic
envelopes. Zero new runtime interactions or fully semantic formats are claimed.

## Gaps and backend requirements

Decode DG_PV through its matching routine; establish texture lookup behavior,
page resolution, coordinates/units, auxiliary-mesh role, and water parameters.
Continue sky/cloud/effect/model extraction and original entity joins. Future
map importers must preserve tree/group/index relationships and cite these
specifications. Do not derive authoritative collision, spawns, respawn, or
access policies from appearance alone. Phase B remains gated by A7.
