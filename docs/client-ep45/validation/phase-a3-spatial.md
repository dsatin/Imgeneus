# A3: dungeon and water extraction

Observation date: 2026-10-02. Status: independently verifiable A3 extraction
completed for two structural families; A3 and A2 remain in progress. Phase B
has not started. Sample executable SHA-256:
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
The [index](../catalogs/spatial-catalogs.json) identifies each original source,
hash, outcome/error, source extent, counts, first/last parts, raw/normalized
export hashes, dependencies, tool hash/version, date, project commit, and
exact command. Large exports remain in ignored `catalogs/spatial-v2/` cache.

## Coverage and reconciliation

| Measurement | Result |
| --- | --- |
| Previously inventoried/extracted archive entries | 23,570; no new extraction or altered originals |
| Spatial family sources verified | 62/62: 47 DG, 12 DG_PV, three WTR |
| Fully structurally decoded files | 50/62: all 47 DG and three WTR |
| Fully structurally decoded families | Two: DG and WTR |
| Unknown DG_PV body outcomes | 12/12 retained with exact errors |
| Source bytes size/hash verified | 206,067,062 |
| Source bytes decoded/reconstructed | 145,803,996 |
| Structural catalog rows | 193,059; includes count/scalar/array parts, not unique entities |
| Dungeon nodes/groups/patches | 2,024 / 22,889 / 23,076 |
| Render vertices/triangles | 3,021,237 / 1,411,815 |
| Auxiliary meshes/vertices/triangles | 1,588 / 165,187 / 158,045 |
| Texture-name records | 3,091: 2,993 DG plus 98 WTR |
| Fully semantically validated formats | Zero |
| Newly validated runtime interactions | Zero |

These geometry measurements overlap catalog rows and must not be added to
unique entity counts. Every vertex/index is a typed JSON value with a
recoverable source offset, rather than a discarded or opaque skipped span.
WLD catalogs remain unchanged; new inner-resource links reference their
verified raw exports and preserve the original entry/hash.

## Integrity and relationships

All 50 decoded sources have full byte consumption, lossless structured
reconstruction, saved-export reconstruction, and read→write→read count checks.
The second run verifies existing deterministic exports without replacement.
Source sizes/hashes agree with the A1 manifest. Twelve bounded loader windows
and four strings reproduce using `objdump` and PE section mappings. No client,
database, account, volume, backend rule, or server image was modified.

The resource catalog contains 3,552 links:

| Link group | Total | Exact matches | Same-stem DDS candidates | Empty names |
| --- | --- | --- | --- | --- |
| WLD water/dungeon names | 86 | 84 | 0 | 2 |
| DG/WTR texture names | 3,091 | 0 | 3,082 | 9 |
| Generated dungeon DDS pages | 375 | 365 | 0 | 0 |
| Total | 3,552 | 449 | 3,082 | 11 |

Thus 3,103 links lack exact matches. This includes the 3,082 DDS candidates,
11 empty names, and ten nonempty missing page candidates. A same-stem filename
is not treated as a successful runtime resource resolution. Those ten page
names belong to four `Login_eternity_territory_01` pages and six `test000_01`
pages. All 22,889 file-local group texture-index candidates are in range;
semantic/rendering validation remains pending. No duplicate target was found
for these links, but the exporter retains all matching archive entry IDs.

WLD inner-resource links reach 44 distinct entries: 41 DG and three WTR.
Six DG entries lack that particular reference. Other placements/routines may
load them; the catalog does not mark them unused. DG_PV activation is unknown.

## Offline verification and fixtures

Command: `python3 -m unittest discover -s tools/ep45-client -p 'test_*.py'`.
Result: **90 tests passed**. New cases test source-fixture hashes/counts,
every prefix of minimal valid layouts, invalid counts at each nested boundary,
zero-vertex omission of triangle fields, nonzero presence flags, child slot
ordering, tool depth bounds, local index bounds/u16 extremes, raw NaN/signed
zero bits, text padding/unknown encoding, malformed reconstruction, retained
source failures, input integrity, resume, and output containment.

`fixtures/spatial-samples.json` contains 27,962 extracted bytes: all three
small WTR sources and two DG leaf spans (308 and 3,542 bytes). Their source
hashes, offsets, lengths, span hashes, and original node paths are recorded.
Only the test envelope is synthetic; it is clearly labeled and never exported
as an original client source. `spatial_fixtures.py` reproduces those selections
from the verified sources/catalog. Tests do not need a running server, network,
database, SDK, or installed client for the new fixtures.

## Outstanding work

The catalog command deliberately exits **1** because all 12 DG_PV candidates
fail the verified DG reader. Its report and complete outputs are still written;
the failure is not hidden or excluded. Unknowns remain: the DG_PV loader/layout,
texture extension lookup, missing pages, node/vertex axes and units, auxiliary
mesh purpose, water parameters, rendering/physics, sky/cloud/effect/model
dependencies, gameplay keys, and runtime behavior. Preserve these gaps for
further A2/A3/A4–A6 analysis. A7 has not released backend implementation.
