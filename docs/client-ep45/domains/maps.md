# Maps and map resources

## Identification and coverage

Specification IDs: `EP45-A3-RESOURCE-001`, `EP45-A3-ZON-001`.
Baseline/hash: [baseline](../baseline.md). Verified sources: 86 WLD files,
`world/TacticsZone.zon`, `WorldMap.cfg`, and other world/terrain/sky assets.
ZON: 35 structurally decoded records. Config: 20 sections, 19 MapNum fields.
Catalogs/tool/commands: [index](../catalogs/resource-catalogs.json),
[`resources.py` 1.0.0](../../../tools/ep45-client/README.md).

## Format and fields

See [resource/map schema](../schemas/resource-metadata.md). WLD signatures and
the first FLD integer are decoded; WLD bodies remain opaque. ZON preserves
all numeric storage and texts; possible coordinates are raw bit values,
with axes/units/semantics unknown. Config keys retain original spelling,
section names, decimal candidate values, raw bytes, and duplicate entries.

## Entities, assets, and relationships

MapNum values can match WLD numeric filenames; these links are `inferred`,
not proven map lookup semantics. Retain every target entry and unresolved link.
No SVMAP was present in the inventoried tree. This does not prove absence of
spawn/portal/position data in WLD or other opaque files. Terrain, collision,
water, region, objects, sky/music, and visible access rules remain pending.

## UI and protocol

Config `Click_*`/`ImgPos_*` names suggest a world-map UI relation; source
keys are evidence, but coordinate meaning and navigation actions require
loader/UI/runtime analysis. Map-change/portal packet contracts are pending.

## Validation

ZON consumes/reconstructs exactly 3,428 bytes. Config line reconstruction is
exact. Bounds, unknown tags, count errors, truncation, raw float bits, and
duplicate-key handling are tested. WLD body decoding and map actions have no
new runtime validation.

## Gaps and backend requirements

Read WLD data and trace actual map IDs, coordinate axes/units, terrain/collision,
included entities, and resource references before world implementation.
No authoritative spawn schedule or portal rule is recovered from a filename.
