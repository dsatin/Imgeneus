# A3 WLD structure and map-content validation

Finding/specification: `EP45-A3-WLD-001`. Observation date: 2026-10-02.
Baseline: `rebirth-evolution-ep45-98c7dd3a`; executable SHA-256
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Phase A remains active. This task extracts/documents maps; it does not release
Phase B or complete all A3 domains.

## Sources and reproducibility

All 86 WLD entries from the hash-bound SAH/SAF manifest remain in the denominator.
[Catalog index](../catalogs/wld-catalogs.json) records each path, source size/hash,
counts, first/last record spans, exports, errors, and tool/dependency hashes.
[Loader evidence](../analysis/wld-loaders.json) indexes 13 bounded disassembly
windows by VA/RVA/file offset and source/disassembly hash. These are inspection
windows, not asserted complete function boundaries. Tool versions are 1.0.0;
GNU objdump's version is recorded in the evidence profile.

[Commands](../../../tools/ep45-client/README.md) reproduce windows and catalogs
from read-only frozen sources. Outputs remain in separate ignored cache folders;
no client, executable, account, database, volume, or server configuration changed.
The initial resource catalog is a historical metadata snapshot; this WLD index
supplies subsequent body extraction.

## Coverage and counts

| Measure | Result | Limit |
| --- | --- | --- |
| Previously extracted archive files | 23,570 | No new SAF extraction in this task |
| WLD source structures | 86/86; zero errors | 55 DUN and 31 FLD variants of one format family |
| Source bytes consumed/reconstructed | 78,903,753/78,903,753 | Grid bodies preserved; numeric terrain semantics unknown |
| Cataloged structural rows | 491,518 | Includes resource records, vectors, points, and trailer rows; not unique entities |
| Placement rows | 463,346 | Indices/storage bits retained; units and runtime loading pending |
| Placement/name-list index candidates | 463,346 matched; zero unresolved | Referenced name ordinals exist; actual loading and full semantics remain unknown |
| Effect rows | 11,287 | Parameter semantics/dependencies pending |
| Portal / named-area candidates | 280 / 553 | IDs, destinations, flags, requirements, UI usage pending |
| Grouped / unknown region records | 62 / 27 | Meanings unknown; not authoritative mob spawns |
| NPC candidate parents / associated points | 2,707 / 779 | Original aggregate 3,486; definition keys/purpose unresolved |
| Music / background sound names | 155 / 861 | Name records, not unique sounds |
| Music zones / sound spots | 201 / 5,796 | One background sound zone has four member cells |
| Filename reference candidates | 5,937 | 5,907 matched; duplicate targets retained |
| Unresolved filename candidates | 30 | 21 empty names and nine nonempty names listed below |
| Fully decoded grid/media payloads | 0 | Widths/hashes are not complete content semantics |
| Fully semantically validated formats | 0 | Structural success does not establish gameplay meaning |
| New runtime interactions | 0 | No gameplay, audio, or repeated session test in this task |

FLD extents are 1024 in 17 sources and 2048 in 14. Those values and the grid
formula reconcile exact spans. Physical units and the executable's in-memory
map-70 override need further analysis.

Nonempty unresolved audio names: `BGM_deatheatertown.wav` (four references),
`Caelumchakra_1F.wav` (two), `Caelumchakra_2F.wav` (one), `bgm_forest01.wav`
(one), and `amb_dike.wav` (one). These lack matches inside candidate archive
roots; that does not prove unplayable sounds or absent features. IDs/offsets
and original text remain in the reference catalog.

## Reader corrections and verification

An initial infrastructure-based probe consumed 56 sources and failed on 30.
Client loader tracing established Mani 44-byte records, Object0 singles plus
pairs, Object1 as a separate section, portal fields with 248-byte second text
and six trailing cells, nested region arrays, and NPC/point aggregate accounting.
No arbitrary byte skips were added to make parsing succeed.
See [field/order evidence](../schemas/wld.md).

Every source passes size/hash comparison, bounded counts, complete consumption,
structured reconstruction, reconstruction from saved raw JSON plus hashed blobs,
and reparse with identical counts. Unknown fields and offsets are retained.
Generation verifies existing output bytes/hashes and refuses replacements.
Structured content is deterministic; report generation times may vary.

A second generation verified existing output content with zero errors.
An independent catalog walk also checked export hashes, required record fields,
unique per-source evidence IDs, source bounds, and reconciled all 491,518 rows.
Placement index coverage is reproduced by summing `name_index_candidates`
across normalized catalogs: matched entries have a target ID; sentinel and
unresolved entries remain explicit. This sample has 463,346 matched candidates.

75 tests pass. WLD additions cover all truncated prefixes of the 688-byte
fixture, unsupported tags, invalid counts/extents, extra bytes, raw float bits,
text padding, 44-byte placements, 76/152-byte Object0 variants, nested groups,
NPC point overruns, exported grid corruption, executable/window binding,
duplicate resource matches, and traversal rejection. Three complete source
fixtures (`Login2.wld`, `106.wld`, `100.wld`) bind entry IDs/hashes and expected
counts. Synthetic inputs are test bytes, never fictional catalog records.

Object0's lists are empty in all 86 sources. Nonempty layouts have executable
and synthetic evidence only. Model indices, map IDs, coordinates, NPC/portal
semantics, resource loading, and playback remain unvalidated at runtime.

## Required follow-up and backend implications

1. Trace `%d.wld` callers, the MapNum config loader, actual map keys, and
   the map-70 override. Preserve original keys and dimensions.
2. Decode grids and auxiliary water/dungeon/sky/model/animation/effect resources.
   Establish axes, units, orientation, collision, and references.
3. Resolve NPC keys against NpcQuest/appearance/service data and associated
   point semantics. Later importers must separate parents from points.
4. Identify portal/region destinations, flags, requirements, and UI/packet
   contracts; do not treat grouped records as mob spawn schedules.
5. Trace missing audio candidates/fallbacks and validate playback/triggers.
6. Continue remaining A3 domains and A2 gaps. A7 still requires complete
   data/UI/protocol coverage and repeated runtime session cycles.

Phase B importers must cite these layouts, separate evidence IDs from original
client keys, preserve optional groups/unknown storage, and report broken
references. Server-only policies remain unknown; implementation decisions
must be documented separately from client evidence.
