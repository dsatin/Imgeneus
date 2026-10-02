# Audio resources

## Identification and coverage

Specification ID: `EP45-A3-RESOURCE-001`. Baseline/hash:
[baseline](../baseline.md). Audio-path catalog: 1,039 sources, preserved by
entry ID/path/hash. Tool 1.0.0, cache exports, and commands:
[index](../catalogs/resource-catalogs.json), [reproduction](../../../tools/ep45-client/README.md).

## Format and fields

RIFF/WAVE chunk trees expose fmt tag, channels, rate, byte rate, alignment,
sample depth, exact fmt bytes, unknown fmt extensions, and data byte counts.
The actual format tag is preserved; no PCM assumption or compressed duration
formula is applied. Audio payloads remain undecoded.

## Entities, assets, and relationships

Paths distinguish candidate background/action/entity sound families without
proving map/mob/skill/action links. Music, ambient, effect, and voice assignments
need loader/path references and runtime events. Preserve original names.

## UI and protocol

No sound trigger or packet/UI effect was newly validated.

## Validation

All source hashes/sizes rechecked. Two files omit odd-chunk padding; full
explicit unpadded walks match source bounds and retain strict-layout errors.
See [anomalies](../catalogs/resource-catalogs.json) and
[schema](../schemas/resource-metadata.md). Runtime playback remains unknown.

## Gaps and backend requirements

Correlate files with map/actions/entities and verify actual playback.
Catalog presence is insufficient to specify a backend-triggered audio effect.
