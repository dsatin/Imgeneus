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
