# Progress and next execution

Active phase: **A — extraction and documentation**. Snapshot date: 2026-10-01.
Phase B has not started under this plan. Earlier experimental adaptations
remain historical test-bench code.

| ID | Work | Status | Deliverable or next action |
| --- | --- | --- | --- |
| A0 | Sample identification | Complete | 18 frozen files plus original executable; PE, hashes, environment, IP patch |
| A1 | SAH/SAF indexing and extraction | Complete | 23,564 tree entries plus six supplemental records; verified hashes/resume; zero errors |
| A2 | Formats and parsers | In progress | Cataloged headers/candidates; decryption and record decoding pending |
| A3 | Content catalogs | Pending | Domain references and explicit gaps |
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

## Next task: A2

1. Confirm the six active SEED containers against client evidence, verify
   decryption/checksums, and retain original bytes.
2. Decode the nine SData sources, starting with items, skills, mobs, NPCs/quests.
   Validate sizes, counts, and relationships. The EP5 fallback is not proof.
3. Document WLD/ZON, assets, and UI formats. Numeric WLD filenames remain
   candidate IDs rather than confirmed logical map identifiers.
4. Produce record catalogs with schemas and evidence. Currently no gameplay
   records have been decoded.

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
All maintained code and text use English; commits stay on the EP45 branch
or its derived branches. Extraction work is committed as `e2bb56bc`.
