# Maps and map resources

## Identification and coverage

Specification IDs: `EP45-A3-RESOURCE-001`, `EP45-A3-ZON-001`, `EP45-A3-WLD-001`.
Baseline/hash: [baseline](../baseline.md); executable
`98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48`.
Observation date: 2026-10-02. Verified sources: 86 WLD files,
`world/TacticsZone.zon`, `WorldMap.cfg`, and other world/terrain/sky assets.
ZON: 35 structurally decoded records. Config: 20 sections, 19 MapNum fields.
All 86 WLD sources (55 DUN, 31 FLD) are structurally decoded; field semantics
and runtime behavior remain incomplete. Catalogs/tools 1.0.0/commands:
[WLD index](../catalogs/wld-catalogs.json),
[resource index](../catalogs/resource-catalogs.json),
[reproduction](../../../tools/ep45-client/README.md).

## Format and fields

See [WLD format/field dictionary](../schemas/wld.md),
[record schema](../schemas/wld-record.schema.json),
[loader windows](../analysis/wld-loaders.json), and
[ZON/config schema](../schemas/resource-metadata.md).
WLD preserves sequential sections, nested counts, exact fixed text, unknown
storage bits, and hashed grid spans. Grid terrain/collision semantics remain
unknown. The client reader requires 44-byte Mani placements, Object0 76-byte
singles and 152-byte pairs, a 248-byte portal text field, nested region groups,
and an NPC aggregate including associated points. ZON preserves
all numeric storage and texts; possible coordinates are raw bit values,
with axes/units/semantics unknown. Config keys retain original spelling,
section names, decimal candidate values, raw bytes, and duplicate entries.

## Entities, assets, and relationships

WLD contains 463,346 placements, 11,287 effect records, 280 portal candidates,
553 named-area candidates, 62 grouped region records, 27 unknown regions,
and 2,707 NPC candidate parents with 779 associated points. These are instance/
evidence counts, not unique definitions or complete gameplay semantics.
Original numeric cells remain unchanged; evidence IDs are entry/section/ordinal
keys rather than substituted client IDs.

Of 5,937 filename links, 5,907 match archived resources; 30 remain unresolved
(21 empty names and nine nonempty audio candidates). Duplicate targets remain
preserved. Music/background names, zones, and spots provide map-to-audio
candidates; playback is unknown.

MapNum-to-filename links remain `inferred`. The executable formats `%d.wld`
from a 16-bit argument, but complete logical map-ID/config linkage is pending.
No SVMAP was present in the inventoried tree. WLD includes entity/region
candidates, so SVMAP absence does not establish absent positions. Terrain,
collision, water, sky, resource loading, and visible access rules remain pending.

## UI and protocol

Config `Click_*`/`ImgPos_*` names suggest a world-map UI relation; source
keys are evidence, but coordinate meaning and navigation actions require
loader/UI/runtime analysis. Map-change/portal packet contracts are pending.

## Validation

ZON consumes/reconstructs exactly 3,428 bytes. Config line reconstruction is
exact. Bounds, unknown tags, count errors, truncation, raw float bits, and
duplicate-key handling are tested. All 78,903,753 WLD source bytes consume/
reconstruct exactly, including reconstruction from saved JSON/blob exports.
Source hashes, counts, extremes, and first/last spans are indexed. Three small
complete client fixtures and synthetic bounds/variant tests run without the
installation. Object0's nonempty variants have static/synthetic evidence only;
all corresponding archive lists are empty. See [WLD validation](../validation/phase-a3-wld.md).
No new map action, NPC interaction, collision, or audio playback was validated.

## Gaps and backend requirements

Resolve actual map/NPC IDs, definition joins, coordinate axes/units, grids,
water/sky/model/effect dependencies, portal destinations/flags, and access
conditions. Map 70 has an in-memory extent override; analyze its behavior before
importing dimensions. WLD records do not establish authoritative spawn
schedules, respawn, drop rates, or service policies. Phase B remains gated by A7.
