# A2 initial report — containers and record structures

Baseline: `rebirth-evolution-ep45-98c7dd3a`. Work branch:
`develop/ep45-data-formats`, derived from checkpoint `8bc252a0`.
Tools: Python standard library; optional system OpenSSL acceleration.
[Commands](../../../tools/ep45-client/README.md).

| Indicator | Result |
| --- | --- |
| SData sources | 13: nine active plus four supplemental |
| Encrypted containers verified | 10: six active plus four supplemental |
| Plain SData sources preserved | 3 |
| Checksum/crypto round-trip failures | 0 |
| Structurally decoded active formats | 5 of 9 |
| Structurally decoded records | 20,037 |
| Semantically validated formats | 0 |
| Runtime scenarios executed in this task | 0 |
| Automated tests | 37 passed, including three optional local-client checks |

[Container report](../catalogs/sdata-containers.json) identifies every source,
SAF offset/hash, decoded path/hash, header, checksum, and padding. The key schedule
and SS tables were identified directly in the frozen executable and are checked
against the [profile](../analysis/seed-profile.json). Function windows show the
default schedule pointer, block loop, and CRC32 routine.

[Backend comparison](sdata-backend-comparison.json) and
[provenance record](sdata-evidence.json) record the verification.
The native and standard-library Python backends produced identical decoded
hashes for all 13 sources. Both verify stored CRC32 and reconstruct all encrypted
source bytes. A repeated run verifies existing decoded outputs without replacement.

[Table report](../catalogs/table-structures.json) records all 13 outcomes, including
four undecoded active formats and four deferred supplemental record layouts.
Five active structures consume all bytes and rebuild identical source content.
Records: items 16,832; mobs 3,001; cash 108; kill-status 60; guild-house 36.
Large raw/normalized JSONL exports stay in cache, with versioned hashes.

Item candidate ID pairs are unique and match all declared groups. Mob logical
IDs remain unknown. Four cash text fields retain undecodable bytes. Numeric
meaning, signedness, units, enums, and references remain unresolved. No existing
EP8 definitions were imported, and no database/service was changed.

## Remaining A2 work

- Decode Skill, NpcSkill, PriestTalk, and NpcQuest records.
- Complete field-use and lookup analysis for the five structural formats.
- Confirm unresolved text encodings, references, resource links, and variants.
- Analyze supplemental usage and remaining backend-relevant WLD/ZON/assets.

Phase A remains active. This initial A2 report does not release phase B or
claim full record semantics, UI coverage, protocol coverage, or client compatibility.
