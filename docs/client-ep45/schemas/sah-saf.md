# SAH/SAF structure observed in this sample

Source: baseline `rebirth-evolution-ep45-98c7dd3a`; hashes in the
[extraction report](../catalogs/extraction-report.json). Infrastructure compared:
Parsec `ebac92c473175a5c0aae29c1e370a2a299d1dedc`, `Sah`, `SFolder`, `SFile`,
and `SBinaryReader`. Actual counts, bounds, bytes, and content hashes provide
sample-specific validation.

## Header and tree

| Offset | Length | Observed field |
| --- | --- | --- |
| 0 | 3 | ASCII `SAH` |
| 3 | 4 | Little-endian signed int32 version, 0 |
| 7 | 4 | Signed int32 declared count, 23,564 |
| 11 | 40 | Padding bytes preserved in report |
| 51 | Variable | Root folder and recursive tree |

Each folder contains an int32-length-prefixed name, file count/records,
and subfolder count/recursive subfolders. Name lengths count bytes including
the observed zero terminator. All sample names passed strict UTF-8 decoding.

File records contain a length-prefixed name, int64 SAF offset, int32 length,
and int32 version. Original bytes/fields/SAH offsets remain in the manifest.
Lengths are **bytes**, verified by exact reads/hashes; the `SFile.Length`
comment mentioning kbs is not used as a unit. Version semantics are unknown.

This SAF does not begin with a `SAF` signature. Access follows index intervals;
do not add/remove a header to compensate.

## Post-tree records and unknown intervals

The tree ends at byte 911,317 of 911,512. The remaining 195 bytes fit exactly:
int32 count 6, six file-shaped records, and final int32 zero, without a folder name.
Names: two `Cash.Sdata`, `Skill.SData`, `Item.SData`, and two `rest space`.
They are extracted separately with `supplemental-*` IDs. Their purpose and
client usage remain unknown; do not substitute them for active tables.

95,141,488 SAF bytes lie outside the union of tree/supplemental intervals.
Their manifest/hash is indexed in the [asset summary](../catalogs/asset-summary.json).
They are not proven useless or recoverable as files. The frozen complete SAF
preserves them for later analysis.

## Duplicate

`Item/3DO/10051__.3do` occurs at ordinals 14,672 and 14,912 with different SAF
offsets. Both contents have 13,204 bytes and SHA-256
`728a400f349ff114a0d0a66f022e41b5fef98e6339f200869a26d5930c880da8`.
Both are preserved. Client lookup precedence is unknown; Parsec dictionary
behavior is not evidence of that precedence.
