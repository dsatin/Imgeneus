# Progress and next execution

Active phase: **A — extraction and documentation**. Last updated: 2026-10-02.
Phase B has not started under this plan. Earlier experimental adaptations
remain historical test-bench code.

| ID | Work | Status | Deliverable or next action |
| --- | --- | --- | --- |
| A0 | Sample identification | Complete | 18 frozen files plus original executable; PE, hashes, environment, IP patch |
| A1 | SAH/SAF indexing and extraction | Complete | 23,564 tree entries plus six supplemental records; verified hashes/resume; zero errors |
| A2 | Formats and parsers | In progress | 10 encrypted containers verified; 8 of 9 active SData sources fully structurally decoded; Skill lacks six expected records; semantics pending |
| A3 | Content catalogs | In progress | 23,570 resource entries; 86 WLD structures; 463,346 placement records; 5,937 resource links; remaining domain semantics/relationships pending |
| A4 | UI and actions | Pending | Screen index and interaction matrix |
| A5 | Static protocol | Partial | Some readers found; complete opcode/direction inventory pending |
| A6 | Runtime validation | Partial | First cycle observed; reentry and other flows pending |
| A7 | Consolidation and exit criteria | Pending | `validation/phase-a-report.md` |
| B0–B8 | Backend implementation | Waiting for A7 | Traceable requirements ordered by dependency |

## A0/A1 results

See the [report](validation/phase-a0-a1.md),
[commands](../../tools/ep45-client/README.md), and
[data sources](catalogs/data-sources.json).

- 172 folders, 23,564 tree entries, and 23,563 unique paths.
- One duplicate path with identical contents; both entries preserved.
- Six supplemental SAH records with unresolved semantics.
- Full 23,570-record manifest in cache; summary and hash versioned.
- Nine active SData files, six with SEED headers; 86 WLD and one ZON.
- 24 `Thumbs.db` files separated from gameplay candidates; ten DDS files have BMP signatures.
- Unreferenced SAF intervals indexed; the complete SAF is preserved.
- 13 integrity/resume/containment tests passed. A second run verified existing
  extracted files against the frozen source.

## A2 initial results

See [initial A2 report](validation/phase-a2-initial.md),
[containers](catalogs/sdata-containers.json), and
[table structures](catalogs/table-structures.json).

- SEED schedule/tables identified in the executable and verified by hash.
- All 10 encrypted sources pass CRC32 and full cipher round trip;
  three plain SData sources are preserved. Native/Python outputs agree.
- Five active record structures decode 20,037 records: 16,832 items,
  3,001 mobs, 108 cash products, 60 kill-status records, 36 guild-house entries.
- Full byte consumption, lossless structured round trip, first/last samples,
  raw/normalized exports, and export hashes are recorded.
- Four cash text fields have unresolved encodings and retain raw bytes.
- Numeric meanings, signedness, units, enums, and links remain unknown;
  zero formats have completed semantic validation. No gameplay test was run.
- 37 tests passed. Initial A2 work was committed as `c507f38a` on
  `develop/ep45-data-formats`, derived from the English checkpoint `8bc252a0`.
  That work is now integrated into `develop/ep45-compatibility`; all further
  compatibility development and commits stay on this single branch.

## A2 extended results

See [extended report](validation/phase-a2-extended.md),
[source outcomes and catalog hashes](catalogs/extended-table-structures.json),
[schemas](schemas/extended-sdata-tables.md), and
[loader evidence](analysis/extended-table-loaders.json).

- Shared Skill/NpcSkill loader confirms nine slots and a 116-byte numeric tail.
- NpcSkill: 3,456 complete records. Active Skill: 3,360 complete records,
  six fewer than expected; source remains `unknown` despite valid CRC/cipher.
- Separate supplemental Skill: 3,366 records, not substituted for the active file.
- PriestTalk: 86 records, all 172 texts retain unresolved encoding; usage unknown.
- NpcQuest: 1,510 NPCs, 2,109 quests, and 637 nonempty matrix arrays out of
  131,072. Matrix rows are not entity counts; semantics remain unknown.
- Cumulative fully decoded active sources: 8/9, containing 27,198 records;
  30,558 complete records including recovery from inconsistent active Skill.
- Exact byte reconstruction and existing-export verification passed.
  The CLI exits 1 deliberately for the Skill discrepancy; failures stay visible.
- 49 tests passed, including extracted first/last NpcSkill fixtures.
  Zero new runtime interactions or semantically validated formats.

## Next A2 tasks

The [pending-work audit](validation/a2-pending.md) confirms static lookup
keys for items/mobs/skills, corrects GuildHouse's final word grouping in a
separate export, and corroborates KillStatus widths. Active/supplemental Skill
comparison found 29 changed shared records plus six additional supplemental
records; substitution is unsupported. Encoding candidates remain unconfirmed.
54 tests pass. Runtime-dependent gaps remain open; independently verifiable
A3 resource catalogs may proceed as authorized by the user.

1. Resolve the active Skill count discrepancy through executable/runtime evidence;
   establish original skill/level lookup keys without substituting source data.
2. Confirm full NpcQuest field reads and PriestTalk usage/encoding; identify NPC,
   quest, list, and matrix lookup semantics and relationships.
3. Trace item/mob field uses and lookup semantics; verify the remaining three
   structural loaders, enums, units, references, and the four cash encodings.
4. Analyze supplemental usage and WLD/ZON/resource semantics. WLD structures
   now decode completely; numeric filenames remain candidate map IDs, while
   terrain/collision units and entity keys still need evidence.
5. Add semantic catalogs and validation evidence; A3 independent resource work
   proceeds with these gaps open, while A7 still gates Phase B.

## A3 initial resource results

The user authorized continuing independent extraction when A2 questions need
additional evidence. See [resource validation](validation/phase-a3-resources.md),
[catalog index](catalogs/resource-catalogs.json), and
[schemas](schemas/resource-metadata.md).

- All 23,570 archive entries have resource rows and rechecked sizes/hashes.
- Recognized metadata/structures: 12,590 files; opaque structures: 10,980.
  Media payloads remain undecoded; no file disappeared from coverage.
- UI-path resources: 997; audio-path resources: 1,039. Two WAV sources omit
  odd-chunk padding; their explicitly parsed variants and strict-layout errors
  remain recorded, with runtime playback unknown.
- 86 WLD prefixes indexed; WLD bodies/terrain/collision/entities remain opaque.
- ZON: 35 structurally decoded records. WorldMap.cfg: 20 sections,
  19 numbered map entries and 19 candidate filename links, with original bytes.
- 63 tests pass, including extracted ZON fixtures. Zero new runtime interactions.
- Next: model/animation/effect/WLD readers, confirmed resource references,
  UI strings/layouts/actions, and static protocol discovery. A2 remains open;
  A7 has not released Phase B.

## A3 WLD and map-content results

See [validation](validation/phase-a3-wld.md), [schema](schemas/wld.md),
[loader evidence](analysis/wld-loaders.json), and
[catalog index](catalogs/wld-catalogs.json).

- 86/86 WLD sources structurally decoded: 55 DUN and 31 FLD; zero errors.
  All 78,903,753 source bytes consume/reconstruct exactly.
- 491,518 structural catalog rows, including 463,346 placements and 11,287
  effect records. These are evidence rows, not unique gameplay entity counts.
- 280 portal candidates, 553 named-area candidates, 62 grouped region records,
  and 27 unknown regions. Their keys, requirements, and server rules remain unknown.
- 2,707 NPC candidate parents and 779 associated points. Their aggregate
  count is 3,486; it must not be treated as a parent count.
- 155 music and 861 background sound names, 201 music-zone records, and
  5,796 sound spots. Playback/trigger behavior remains unvalidated.
- 5,937 filename links: 5,907 matched archive targets; 30 unresolved,
  consisting of 21 empty names and nine nonempty missing candidates.
- Raw JSON, normalized JSONL, and hashed grid blobs stay in cache. Saved
  exports reconstruct the sources; repeated generation verifies existing outputs.
- 75 tests pass, with three complete small WLD source fixtures and synthetic
  tests for nested counts, 44/76/152-byte variants, portal boundaries, corruption,
  and blob integrity. No new runtime interactions or fully semantic formats.
- Next: trace map/entity IDs, coordinate/terrain units, water/sky/effect/model
  dependencies, NPC-definition links, and remaining A3 domains. Keep the A2
  runtime-dependent questions open. Phase B continues to wait for A7.

## Outstanding experimental work

- Reentry after logout: the bench sent logout/list/faction, but no second
  character-selection packet was observed. The cause is unconfirmed.
- Experimental character-selection writer: prepared but neither compiled
  nor run. No client outcome validates this additional change.
- Initial inventory adapted; item movement and other legacy packet layouts
  still need comparison.
- Client quickbar and server structures appear different; document builders
  and readers before changes.
- Existing server seeds/data were not extracted from this sample.

## Maintenance

For each task record outputs/counts, evidence sources, reproducible commands,
limits, and next steps. Separate inventory, extraction, decoding, and runtime
validation. Switch to B only when the A7 report meets the AGENTS.md criteria.
All maintained code and text use English; commits stay on
`develop/ep45-compatibility`. Extraction work is committed as `e2bb56bc`.
