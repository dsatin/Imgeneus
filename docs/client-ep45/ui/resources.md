# UI resource inventory

Reference ID: `EP45-A3-UI-RESOURCES-001`. Baseline/hash:
[baseline](../baseline.md). The current catalog contains 997 UI-path resources
with entry IDs, original paths, source hashes, dimensions where readable, and
explicit unknown payloads. [Export index](../catalogs/resource-catalogs.json),
[schema](../schemas/resource-metadata.md), [reproduction](../../../tools/ep45-client/README.md).

Source filenames include skill/quest assets and auction/friend resources.
Preserve exact spellings, including `auction_buy_search_botton.tga`,
`auction_completio.tga`, and names with spaces. A filename is evidence that
the resource exists, not proof of a reachable action or backend service.

WorldMap.cfg preserves 19 numbered groups with MapNum, Click, and ImgPos keys;
their loader/navigation links remain pending. Font resources, layouts,
controls, strings, panel functions, complete state transitions, and errors
require additional analysis. A4 screen/action coverage is not implied by
these 997 files. No new UI interaction was tested.
