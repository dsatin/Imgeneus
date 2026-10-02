# A3 initial resource catalogs

Report ID: `EP45-A3-RESOURCE-001`. Observation date: 2026-10-01.
Project checkpoint: `9616ac73`. Baseline and executable SHA-256:
[baseline](../baseline.md). Archive manifest SHA-256:
`141493242b496dde8119fb30b45e84fe078b04ddbf957d2226ac1c92a28902cf`.
Tool: `resources.py` 1.0.0; exact tool/dependency hashes, export paths/counts,
source anomalies, and candidate links: [machine-readable index](../catalogs/resource-catalogs.json).
[Schemas](../schemas/resource-metadata.md), [reproduction](../../../tools/ep45-client/README.md).

## Coverage

| Measure | Result |
| --- | --- |
| Source archive entries cataloged and size/hash rechecked | 23,570/23,570, including duplicate and supplemental entries |
| File verification/reader errors | 0 |
| DDS headers | 10,451 |
| BMP headers | 39, including ten `.dds` paths with BMP signatures |
| Candidate TGA headers | 973 |
| WAVE chunk metadata | 1,039; two explicit unpadded source variants |
| WLD prefixes | 86; bodies remain opaque |
| Sources with recognized metadata/structures | 12,590 |
| Other source files with opaque structures | 10,980; all remain cataloged |
| UI-path resources | 997 |
| Audio-path resources | 1,039 |
| ZON records structurally decoded | 35/35 |
| WorldMap.cfg sections | 20: one header plus 19 numbered sections |
| Candidate MapNum-to-WLD links | 19, with source offsets and target entry IDs |
| Media payloads fully decoded | 0 |
| New runtime interactions validated | 0 |

Metadata totals are source-file counts, not cataloged game entities or
completed semantic formats. UI assets do not imply screen/action coverage.
Path-based groups remain inference labels, not loader-proven relationships.

Two WAVE sources omit odd-chunk padding. Strict parsing identified the
discrepancy; the separately labeled unpadded layout consumes both complete
files. Original standard-layout errors remain recorded, with playback unknown.
No file was repaired or replaced. Unknown fmt extension bytes are exported.

ZON format 5 and WorldMap.cfg reconstruct exactly. ZON retains unknown float
bits/text encodings and has no confirmed axis/map/region semantics. Config
keeps every raw line, repeated field, original section, and leading-zero value.
MapNum-to-numeric-WLD matches are inferred filename links; they are not proven
map lookup or teleport contracts.

63 tests pass, including extracted first/last ZON fixtures, invalid tags/counts,
truncation/extra bytes, repeated config keys, raw numeric bits, RIFF bounds,
unpadded variants, and signature-over-extension handling. The complete final
catalog command succeeds; large exports stay excluded from Git/Docker.

## Remaining work

A3 remains in progress. Decode and trace models/skeletons/animations/effects,
WLD terrain/collision/entities, fonts/strings/layouts, audio triggers, and
item/character/mob/NPC resource relationships. Continue A4/A5 static discovery
where independent, and collect controlled runtime evidence for A2/A6 gaps.
A2 stays in progress as recorded in [pending work](a2-pending.md). A7 has not
released backend implementation.
