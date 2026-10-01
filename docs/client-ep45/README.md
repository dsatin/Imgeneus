# EP 4.5 client reference

This directory is the specification source for compatibility with the locally
installed Rebirth Evolution test client. Identification and SAH/SAF extraction
are complete: 23,564 tree entries and six supplemental records, with verified
hashes. Ten encrypted SData containers are verified and five active table structures
are decoded. Field semantics, remaining data, assets, UI, and protocol remain
in phase A. No EP8
gameplay rule has been imported as evidence.

The detailed work order is in [AGENTS.md](../../AGENTS.md): extract and document
the client first, then implement the backend.

| Reference | Purpose |
| --- | --- |
| [Progress](progress.md) | Active phase, tasks, exit criteria |
| [Baseline](baseline.md) | Identified sample and snapshot limits |
| [Catalogs](catalogs/README.md) | Manifests and exports |
| [Domains](domains/README.md) | Data and relationships to extract |
| [UI](ui/README.md) | Screens and action matrix |
| [Protocol](protocol/README.md) | Initial findings and outstanding contracts |
| [Analysis](analysis/README.md) | Executable anchors and reproduction |
| [Validation](validation/README.md) | Integrity, coverage, exit criteria |
| [Backend](backend/README.md) | Derived requirements and later implementation |
| [Domain template](templates/domain.md) | Documentation standard |
| [Evidence schema](schemas/provenance.schema.json) | Finding provenance |
| [Tools](../../tools/ep45-client/README.md) | Reproducible commands and tests |
| [A0/A1 report](validation/phase-a0-a1.md) | Identification and extraction results |
| [SAH/SAF format](schemas/sah-saf.md) | Observed structure and unknown fields |
| [A2 initial report](validation/phase-a2-initial.md) | Container and record-structure coverage |
| [SEED format](schemas/sdata-seed.md) | Client constants, checksums, round trips |
| [Table structures](schemas/sdata-tables.md) | Lossless record layouts and unresolved semantics |

Raw files and large exports belong in the ignored `.client-ep45-cache/`.
Tools live in `tools/ep45-client/` and accept the client path as a parameter.
The loose-file manifest and internal archive inventory are separate outputs.

All authored code and prose use global English. Raw client strings, filenames,
and bytes retain their original values as evidence. Status values use English
as defined in the evidence schema. Earlier Portuguese status labels were
replaced without changing raw data; the previous full manifest is preserved
as `archive-files.v1.jsonl` in cache.

Runtime validation requires a recorded scenario and result. A static finding
does not establish an original server rule. Documented gaps remain part of
this reference.
