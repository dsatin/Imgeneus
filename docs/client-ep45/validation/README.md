# Validation and exit criteria

Report separately: inventoried/extracted files, decoded formats, cataloged
entities, identified screens/actions, mapped opcodes, executed scenarios,
and scenarios accepted by the client. State denominators and include errors.

[Extended A2 validation](phase-a2-extended.md) records eight of nine active
SData sources fully structurally decoded and Skill's six missing expected
records. It separates recovered records, supplemental data, and matrix arrays
from fully validated source coverage. No new runtime interactions are claimed.

[A3 WLD validation](phase-a3-wld.md) records 86/86 structures, source/export
reconstruction, map content counts, and resource links. It distinguishes
491,518 structural rows from unique gameplay entities and leaves terrain,
field semantics, original keys, and runtime behavior as explicit gaps.

[A3 dungeon/water validation](phase-a3-spatial.md) adds 50/62 structurally
decoded source outcomes across two families, complete typed mesh arrays,
verified export reconstruction/resume, and 3,552 dependency links. All 12
DG_PV failures and unresolved links remain visible. Ninety tests pass; no new
runtime interaction or completed semantic format is claimed.

## Extraction integrity

- Reconcile declared SAH counts with all actual entries.
- Validate SAF interval bounds and actual bytes read.
- Verify source/output hashes, duplicates, and case/path collisions.
- Check record counts/offsets, full file consumption, and relationships.
- Reproduce outputs using the same tools and parameters.

## Behavior coverage

Create `compatibility-matrix.csv` linking feature/action, data/UI/protocol
specification, evidence, implementation, scenario, and outcome. First entry
and logout were observed; reentry failed. Other systems remain unvalidated.

Basic scenarios include same/different characters after logout, repeated
logout, disconnect/reconnect, and restart. Then exercise inventory/equipment,
NPCs/portals, combat/skills/quests, economy/social/PvP, and every new feature.

## Implementation gate

`phase-a-report.md` must demonstrate every A7 criterion in AGENTS.md, identify
blocking gaps, and distinguish data absent from the client. Do not start B
while required binary formats remain unknown. Document unavailable server
rules and required implementation decisions rather than demanding their recovery.

The additional selection writer has no build/runtime result. Earlier inventory
and disconnection checks passed on a prior image; they do not validate that writer.
