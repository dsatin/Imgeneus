# A2 pending-work audit

Audit ID: `EP45-A2-AUDIT-001`. Date: 2026-10-01. Baseline executable:
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Project checkpoint: `f0b49513`. [Reproducible audit outputs](a2-audit.json),
[static contracts](../analysis/table-lookup-profile.json),
[commands](../../../tools/ep45-client/README.md).

## Findings resolved in this audit

- **Item lookup:** `0x461450` selects one-based group and record arguments
  from two byte-sized keys. All 16,832 stored first-byte/second-byte pairs
  match those positions. This validates the static lookup keys, not every
  item field or inventory packet.
- **Mob lookup:** `0x461990` uses a zero-based uint16 index and object stride
  `0x2c`, bounded by the stored low-16-bit record count. A separate name search
  also exists. Export 3,001 index keys without assuming on-wire IDs.
- **Skill/NpcSkill lookup:** `0x462350` uses one-based uint16 group and byte
  slot 1–9, object stride `0x88`. The first serialized tail byte is not the
  address-selection key. NpcSkill has 384 first-byte values of 1 and 3,072
  values of 0; do not renumber/drop slots based on that byte.
- **GuildHouse field widths:** the executable reads three four-byte headers,
  36 records of five bytes plus **five two-byte values**, and 24 trailing
  four-byte values. The earlier `BBBBBhhhhBB` reader incorrectly split the
  final word, despite its identical byte length and successful round trip.
  Corrected `BBBBBHHHHH` exports retain all 36 records and original source
  bytes under `EP45-A2-GUILD-002`. Old outputs remain historical evidence.
- **KillStatus structure:** bounded executable reads corroborate one byte,
  four bytes, two bytes, and six byte/word pairs per record. Field meanings
  remain unknown.

The lookup exports use `EP45-A2-LOOKUP-001`, retain source-record IDs and
original values, and explicitly distinguish static keys from unproven packet
IDs. Fully semantically validated formats remain zero.

## Remaining gaps and how to continue

| Gap ID | Review result | Required evidence | Independent work allowed |
| --- | --- | --- | --- |
| `A2-GAP-SKILL-END` | Six records are absent from the active source; supplemental has six extra **and 29 changed shared records**, so appending/replacing is unsupported | Observe loading bounds and downstream accesses in a controlled runtime session; establish whether unavailable slots are reachable | Inventory resources, maps, UI strings, and other domains |
| `A2-GAP-SUPPLEMENTAL` | Supplemental active use remains unknown; complete source comparison is now exported | Trace actual archive resolution/loading and selected content buffers | Keep each source separate; continue independent catalogs |
| `A2-GAP-ENCODING` | All 172 PriestTalk unknown texts round-trip as CP949, but also CP1252; four cash and six NpcQuest unknown texts round-trip as CP1252, not CP949 | Trace conversion code/code-page selection and visible original strings | Preserve original bytes; use candidate side views only |
| `A2-GAP-PRIEST-USE` | File structure decoded; dedicated loader and runtime usage unresolved | Trace filename construction/UI references or read buffers | Resource inventory and static UI mapping |
| `A2-GAP-NPC-QUEST` | Layouts consume whole source; full field uses, IDs, list/matrix meaning and references unresolved | Complete loader/lookup tracing and controlled NPC/quest actions | NPC/quest resource and candidate-reference indexing |
| `A2-GAP-TABLE-SEMANTICS` | Item/mob/skill address keys improved; stats, enums, units, timing and remaining Cash reads unresolved | Individual field-use chains and runtime comparison | Asset catalogs and explicit unknown relationships |
| `A2-GAP-WORLD-ASSETS` | 86 WLD, one ZON, WorldMap.cfg, and other resource formats remain only inventoried | Bounded readers, source/loader comparisons, reference validation | Start A3 resource catalogs from verified archive entries |

No static evidence in this audit resolves the active Skill shortage or proves
an encoding's runtime selection. The byte-decoding questions cannot be filled
with EP8 data or other server references. Runtime-dependent gaps remain open,
with concrete next tests, rather than stopping all extraction work.

The user authorized continuing independent tasks when A2 gaps cannot be
resolved. A3 resource catalog work may proceed while A2 remains **in progress**.
A7 still requires all blocking contracts to be resolved; this audit does not
release Phase B. No client file, database, account, or service was changed.

## Validation

54 tests pass, including corrected word widths, truncation, positional keys,
content comparison across different source offsets, and conservative encoding
candidates. Exact tool/input/export hashes are in the audit JSON. The initial
catalogs are not overwritten. Zero new runtime interactions were executed.
