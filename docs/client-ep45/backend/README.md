# Implementation after extraction

Phase B waits for documented A7 completion. Preserved experimental code
serves as history/test-bench infrastructure and does not change the work order.

Each future requirement needs an ID/domain, client sources, data/packet
contracts, preconditions, observable behavior, persistence, test scenarios,
and status. Distinguish absent client information from incomplete extraction.

| Order | Deliverable | Dependency |
| --- | --- | --- |
| B0 | EP4.5 profile and EP8 boundaries | Consolidated specification |
| B1 | Schema, migrations, catalog importers | Extracted IDs/relationships |
| B2 | Login/World, characters, session cycles | Validated protocol/states |
| B3 | Maps, presence, movement, entities | Map/asset/entity catalogs |
| B4 | Stats, items/equipment, storage | Items, slots, limits, formats |
| B5 | Skills/buffs, combat/PvE, quests | Data and documented gap policies |
| B6 | Economy, social, PvP | Client flows/systems |
| B7 | Complete coverage and repeated tests | All discovered features |
| B8 | Linux operations and delivery | Demonstrated coverage and limitations |

Existing boundaries: networking/encryption in `Imgeneus.Network`, persistence
in `Imgeneus.Database`, definitions in `Imgeneus.GameDefinitions`, gameplay
in `Imgeneus.Game`, handlers/serializers in `Imgeneus.World`/`Imgeneus.Login`.
Compare these modules with specifications. Their seeds and EP8 formats are
not source data from this client.

Drop/respawn/AI/formula policies without client evidence belong in separate
policy documents with configuration/tests. Observable compatibility does
not recover original server code.

Future map requirements also depend on `EP45-A3-SPATIAL-001`:
[dungeon/water structures](../schemas/spatial-resources.md) and
[integrity/gaps](../validation/phase-a3-spatial.md). Importers must preserve
file-local tree/group/index relationships and every raw unknown field. The
auxiliary meshes have no established authoritative collision role; water
parameters have no established gameplay units. DDS candidates, DG_PV layouts,
and missing page references require further extraction/validation before
being used as backend contracts. These are dependencies for phase B, not
implemented rules or evidence of original server behavior.
