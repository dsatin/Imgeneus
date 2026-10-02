# Executable analysis

Known addresses belong to the sample in `../baseline.md`. Do not reuse offsets
on another executable without verification.

| Virtual address/file offset | Observation |
| --- | --- |
| VA `0x5867F0` | Dispatch for multiple received World packets |
| VA `0x57C790` | Character-list reader |
| VA `0x57CC60` | Initial-inventory reader |
| VA `0x57CE8D` | Observed inventory fault instruction |
| VA `0x580A00` | Quickbar reader for `0x010B` |
| VA `0x401570` / `0x4015A0` | Entry/logout decryption-mode functions |
| File offset `0x2A9B84` | Locally patched English Login address |

Read PE sections before address conversion: RVA, virtual address, and file
offset are distinct. Record architecture/base, binary hash, and tool version.

Limited read-only inspection:

```bash
EP45_CLIENT_DIR='/path/to/RebirthEvolution'
objdump -h "$EP45_CLIENT_DIR/game.exe"
objdump -d -Mintel --start-address=0x57c790 --stop-address=0x57ca50 "$EP45_CLIENT_DIR/game.exe"
```

Keep full disassembly in cache. Publish only relevant excerpts and function/
evidence maps. Explain dynamic scenarios and correlate UI actions with
functions. Strings and historical backend names are clues, not semantic proof.

A2 adds [crypto constants](seed-profile.json) and [bounded loader/function windows](sdata-functions.json).
Full disassembly stays in cache; addresses, source-byte hashes, inspection bounds,
and reproduction commands are indexed without claiming complete function boundaries.

[Extended loader evidence](extended-table-loaders.json) records 84 Skill tail
reads, nine-slot allocation, NpcQuest matrix bounds, quest-reader calls, and
two observed numeric loading transformations. Original exports retain raw
values. PriestTalk usage and complete NPC/quest field semantics remain unknown.

[WLD loader evidence](wld-loaders.json) indexes 13 windows from the same
executable. The [WLD format](../schemas/wld.md) links reads to 44-byte Mani
placements, Object0 singles/pairs, portal text boundaries, nested regions,
and NPC aggregate accounting. `wld_loaders.py` reproduces windows using PE
section mappings and hashes; `wld.py` verifies that evidence before extraction.
Full map IDs, axes/units, field semantics, and runtime behavior remain pending.

[Dungeon/water loader evidence](spatial-loaders.json) adds 12 windows and four
exact strings from the same executable, reproduced by `spatial_loaders.py`.
[Spatial formats](../schemas/spatial-resources.md) tie DG nodes/groups/patches,
44-byte render and 12-byte auxiliary vertices, u16 index arrays, and WTR fields
to actual read sites. `spatial.py` binds window/string hashes before decoding.
DG_PV variants, DDS extension lookup, and runtime activation remain unknown.
