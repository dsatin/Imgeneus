# Visual and auxiliary resources

## Identification and coverage

Specification ID: `EP45-A3-RESOURCE-001`. Baseline/hash:
[baseline](../baseline.md). All 23,570 archive entries are cataloged and
rechecked against extracted content hashes. Full, UI, audio, and map JSONL
exports remain in cache, indexed by [counts/hashes](../catalogs/resource-catalogs.json).
Tool: `resources.py` 1.0.0; [commands](../../../tools/ep45-client/README.md).

## Format and fields

[Resource schema](../schemas/resource-metadata.md) documents bounded image,
audio, map-prefix, ZON, and config readers. Original path/entry IDs, source
spans, unknown bytes, and metadata are retained. DDS/BMP signatures override
extension guesses. Candidate TGA and path classifications remain inferred.

## Entities, assets, and relationships

The complete file catalog preserves duplicate entries. No model ID, animation
index, equipment/mount relation, skeleton layout, or entity-to-texture link has
been invented. Models, skeletons, animation/effects, clothing, emblems, and
additional resources are cataloged as sources pending structural readers.

[WLD structures](../schemas/wld.md) now catalog 463,346 placement records and
11,287 effect records. Filename links use roots passed by the client loader
and retain original source text/indices and duplicate targets. Asset bodies,
transform units, dependencies, and runtime rendering still require analysis.

## UI and protocol

UI resource names/dimensions provide discovery clues. They do not prove that a
panel is reachable, that a button sends a packet, or that the client accepts a
backend response. See [UI resource reference](../ui/resources.md).

## Validation

File hashes/sizes verified, all entries retained, metadata bounds checked,
source anomalies identified. No pixel/mesh/audio payload or runtime interaction
is claimed as fully decoded/validated by this catalog.

## Gaps and backend requirements

Trace loaders and asset paths, confirm model/animation/effect structures,
then resolve resource relationships and rendering/session requirements.
Opaque resources remain explicit gaps, rather than assumed absent features.
