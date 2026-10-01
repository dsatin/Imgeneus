# A0/A1 report — identification and extraction

Executed 2026-10-01 from project base `eacfc1d6`, Python 3.14.7,
baseline `rebirth-evolution-ep45-98c7dd3a`. Backend/databases were unchanged.
Extraction tools and evidence were committed as `e2bb56bc`.

| Indicator | Result |
| --- | --- |
| Frozen external files | 18 plus original pre-patch executable |
| Declared/read SAH tree entries | 23,564 / 23,564 |
| Tree folders | 172 |
| Unique tree paths | 23,563 |
| Supplemental post-tree records | 6 |
| Extracted and verified entries | 23,570 |
| Tree content bytes | 2,385,899,048 |
| Extraction/bounds/path errors | 0 |
| Tree interval overlaps | 0 |
| Duplicate paths | One; both identical contents preserved |
| Automated tests | 13 passed |
| Gameplay records decoded at A1 | 0 |

A second run verified existing extraction against `originals/`, retaining
raw files and comparing each output hash with its SAF interval. Complete
SAH/SAF hashes were checked before and after each run.

## Outputs and reproduction

- [Identification/PE/runner](../catalogs/baseline-evidence.json).
- [Current external manifest](../catalogs/loose-files.current.json); prior
  manifest retained, only `CONFIG.INI` differs.
- [Extraction report](../catalogs/extraction-report.json): source/tool hashes,
  counts, classifications, checks, and full-manifest hash.
- [Data sources](../catalogs/data-sources.json), [maps](../catalogs/map-files.json),
  [assets/anomalies](../catalogs/asset-summary.json).
- Full cache index: `archive-files.jsonl`, 23,570 records. Its current hash
  is recorded in the extraction report. Previous Portuguese-status manifest
  is preserved as `archive-files.v1.jsonl`, SHA-256
  `09240d9b290aded79f66f40991e62cca19aca5eab90792d1f1f8b584fe847a29`.
- [Commands and tests](../../../tools/ep45-client/README.md).

## Identified content, not decoded at A1

Nine active SData files: Cash, KillStatus, Skill, Item, NpcSkill, Monster,
GuildHouse, PriestTalk, NpcQuest. Six have SEED-associated headers. A1
cataloged declared sizes/alignment; it did not validate decryption/checksums.

86 WLD and one ZON were found, with no `.svmap` index entries. This does not
exclude position data in other formats. Numeric WLD names are only candidate IDs.

Path classification finds 997 UI assets and 1,039 audio files, not enumerated
screens/controls/interactions. 24 compound-file `Thumbs.db` entries are separated
from gameplay candidates. Ten `.dds` entries have BMP signatures; readers
must follow actual content structure.

## Limits and next phase

A0/A1 are complete for sample identification and indexed-file extraction.
Supplemental-record semantics and unreferenced intervals remain unknown,
with bytes preserved in the frozen SAF. No authoritative rule or other-episode
table was imported.

A2 must validate containers/decryption and record layouts before content,
UI, and protocol catalogs. Phase A is not complete; this report does not
release phase B. English status migration changes metadata hashes only,
not source or extracted-content hashes.
