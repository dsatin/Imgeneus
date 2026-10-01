# SEED SData container

Specification ID: `EP45-A2-SEED-001`. Baseline:
`rebirth-evolution-ep45-98c7dd3a`, executable SHA-256
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Source hashes/results: [container report](../catalogs/sdata-containers.json).
Reproduction: [tool commands](../../../tools/ep45-client/README.md).

## Binary layout

| File offset | Length | Field |
| --- | --- | --- |
| 0 | 40 | ASCII `0001CBCEBC5B2784D3FC9A2A9DB84D1C3FEB6E99` |
| 40 | 4 | Little-endian CRC32; zero selects the infrastructure's shifted-header candidate |
| 44 | 4 | Little-endian decoded byte count, or CRC32 for the shifted candidate |
| 48 | 16 | Header bytes; shifted candidate instead has length at 48 and 12 remaining header bytes |
| 64 | Multiple of 16 | Independently transformed SEED blocks |

The six active and four supplemental encrypted sources in this sample use
checksum offset 40. The shifted form is supported/tested as an infrastructure
candidate, not a confirmed variant of this sample. A legitimate zero CRC32
in another variant could make that heuristic ambiguous; analyze such a
sample before selecting a layout.

Decoded size must fit the aligned payload with 0–15 alignment bytes. Original
header bytes and decrypted alignment bytes are preserved in the report.
CRC32 covers only the declared decoded bytes. Unknown padding is not discarded
from evidence or assumed to be zero.

## Executable evidence and transform

[Crypto profile](../analysis/seed-profile.json) records source offsets/hashes:
128-byte expanded round-key schedule at file offset `0x2f9148`, VA `0x6f9148`;
4,096-byte SS tables at file offset `0x2f92d0`, VA `0x6f92d0`.
Tools verify the complete executable hash and both segment hashes before use.
Constants are read from the executable; no Parsec constants or session keys
are embedded in project code.

[Function windows](../analysis/sdata-functions.json): `0x5ae1c0` selects the
default schedule `0x6f9148`, loops through 16-byte blocks, and calls `0x5b4640`.
`0x5ae110` computes reflected CRC32 using a table at `0x6f8d48`, with initial
and final complements. The Monster loader at `0x4615a0` reads a 64-byte header,
calls the transform, and compares the computed checksum before record parsing.

Each block has four big-endian 32-bit words. Decryption applies the 16 SEED
rounds in reverse expanded-key order; schedule words and SS constants are
read little-endian from the executable. Results match every stored CRC32.
Decrypting and re-encrypting the entire aligned payload reproduces every
source encrypted byte, including padding.

The optional system OpenSSL backend must agree with the reference Python
transform on three different test blocks in both directions before selection.
Each actual payload also compares first/last decrypted blocks with Python.
`--backend python` uses only the standard library and reproduces identical
outputs for all 13 SData sources. Original and existing decoded files are
never replaced; divergent existing outputs cause an explicit error.

## Scope

Ten encrypted containers are statically validated; three sources have no
SEED header and are copied unchanged. Container validation does not validate
record layouts, field meanings, UI actions, or server rules. Supplemental
records remain separate because their purpose is unknown.
