# Snapshot baseline

## Project

Existing fork: <https://github.com/dsatin/Imgeneus>.
Working branch: `develop/ep45-compatibility`.
Linux base: `63e0248ab148481dabe8394a34edd06720525b09`.
Preserved `master`: `0ce355594d521c3a06a08f24d0a9b60ebc8a459f`.

| Submodule | Commit |
| --- | --- |
| Imgeneus.Authentication | `77b3a65e9a0ba60f83e1aa452e9f0b997ea27a70` |
| LiteNetwork | `3dad300d984abae0c2aee53f0054683353023181` |
| Sylver.HandlerInvoker | `6b8edfb704ea5a28eb9663ed6c39c08d8f62e2b0` |
| Parsec | `ebac92c473175a5c0aae29c1e370a2a299d1dedc` |

Linux infrastructure adaptations are described in [deploy/README.md](../../deploy/README.md).
Docker applies submodule patches during builds. No global .NET SDK is installed
on this machine; inventory/extraction tools use Python 3 without SDK or Docker.

## Client

The user identifies this installation as EP 4.5, Rebirth Evolution:

```text
/home/dsatin/Games/Heroic/Prefixes/Shaiya EP 4.5/drive_c/RebirthEvolution
```

| File/variant | SHA-256 |
| --- | --- |
| Original `game.exe`, before IP patch | `45755d927ee66c7c5e354defb5e8f9329f8f21848307e62797f368dee2c33f91` |
| Local-IP `game.exe`, checked 2026-10-01 | `98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48` |
| `data.sah`, checked 2026-10-01 | `6ad31356e94e243b45d4f4a6ffe881d76dd945a0e4f7f22687ebdf6026bf7f3c` |
| `data.saf`, inventoried 2026-10-01 | `e3c7f3a8268d5242b6199b99ca482c3390fc012fad2257dd155b1e35794d5e7b` |

The executable is PE32/x86. Sizes: executable 3,219,456 bytes, SAH 911,512 bytes,
SAF 2,487,238,964 bytes. The external manifest records loose-file hashes/sizes;
the [A0/A1 report](validation/phase-a0-a1.md) documents the internal archive.

`Version.ini` declares `CheckVersion=3`, `CurrentVersion=5`, and
`StartUpdate=UPDATE_END`. These values do not prove the episode.

The local patch changed only the embedded English-client Login address at
file offset `0x2A9B84`: a 16-byte slot containing `92.55.147.107`, replaced with
zero-padded `127.0.0.1`. EP8-style IP arguments did not replace this address in
the observed test. Historical successful launch arguments were `start game`.
Other executables may use different addresses and offsets.

Session environment: Manjaro, Heroic, GE-Proton, local Login TCP 30800 and
World TCP 30810. Never publish credentials or complete account configuration.

### A0 frozen sample

The 18 current loose files were copied into cache `originals/`, verified by
SHA-256, and set to mode 0444. The pre-patch executable is preserved separately
as `game-original.exe`. The [current manifest](catalogs/loose-files.current.json)
differs from the preceding manifest only in `CONFIG.INI`; executable/SAH/SAF
hashes are unchanged. Extraction did not modify source files.

[Identification evidence](catalogs/baseline-evidence.json): PE32, machine
`0x14c`, image base `0x00400000`, COFF timestamp `2010-07-12T03:56:25Z`.
The internal timestamp differs from 2011 file dates; neither proves episode.
Comparison confirms 11 changed bytes, all within the 16-byte Login slot,
with no file-size change.

Recorded environment: Python 3.14.7, Linux 7.2.3-2-MANJARO, glibc 2.44,
GE-Proton11-5. Local `flatpak info com.heroicgameslauncher.hgl` reported Heroic
v2.22.1. Evidence records only allowlisted runner settings. English UI language
was observed in earlier sessions rather than inferred from directory names.

Historical scenario: launch the local-IP executable with `start game`,
authenticate using a local test account, select/create a character, enter the
map, and log out. Trying the same character after return to selection produced
the reported failure. This inventory execution did not repeat gameplay tests.

## Observations and pending validation

| Item | Evidence/status |
| --- | --- |
| Login/character creation | Confirmed by the user with the local-IP client |
| First-entry crash | Wine fault at `0x0057CE8D`; reader `0x57CC60` consumed smaller records than EP8 sent |
| Initial inventory | 34-byte writer with bag/slot limits; earlier build checks passed |
| Send after disconnect | Disposed/disconnected socket guard; earlier build check passed |
| First map entry | User confirmed; logs recorded `CHARACTER_ENTERED_MAP` |
| Logout | User confirmed; logs recorded removal and `LOGOUT` |
| Second entry in the same session | Failed; no second `SELECT_CHARACTER` in observed logs |
| EP4.5 character selection | Additional writer based on `0x57C790`; not compiled/tested |
| Other features | Not comprehensively validated with this client |

The snapshot contains experimental code beyond the running World image.
Builds of the additional selection change were interrupted before starting;
there is no valid build result. Documentation and extraction require no service restart.

The historical option is `WorldServer:LegacyInventoryPackets`, configured
with `WORLD_LEGACY_INVENTORY`. In source it also selects the experimental
character-list writer. Its default remains `false`. Phase B must replace this
experiment with a defined protocol profile.
