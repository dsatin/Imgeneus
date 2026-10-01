# Imgeneus: EP 4.5 client compatibility

## Objective and mandatory work order

Build a backend compatible with the locally installed EP 4.5 client, using
that client exclusively as the specification source. Inventory, extract,
analyze, and document its contents and expectations first. Start backend
implementation only after verifiable completion of this work. Coverage
includes data, UI, graphics, audio, protocol, and session states. Entering a
map alone does not demonstrate complete compatibility.

Before working, read `docs/client-ep45/README.md`, `progress.md`, `baseline.md`,
and the references for the affected domain. Update progress and record
evidence after each task. The active phase is recorded in `progress.md`;
it is currently **A — extraction and documentation**.

### Language and branch policy

All maintained code, comments, documentation, schema labels, tool messages,
and commit messages must use global English. Preserve original client
strings, filenames, and raw bytes verbatim as source data; identify their
encoding and language separately. Do not translate evidence in place.

Create commits only on `develop/ep45-compatibility` or its derived branches.
Preserve `master` and `develop/linux-server`. Never force-push or rewrite
the base of this initiative. Commit existing work before starting the next
extraction task; do not create an empty commit for work already committed.

### Accepted sources

- The target executable, DLLs, loose files, `data.sah/data.saf` entries,
  text, images, sounds, UI, and observed client behavior.
- Static analysis, debugging, and the client's traffic against our server
  or a local test bench. Buffers captured after decryption are evidence.
- Parsec, analysis tools, and existing code may provide infrastructure.
  They do not prove that a format or rule belongs to this EP 4.5 client.
- Do not fill gaps with packets, SQL, data, formulas, or documentation from
  other episodes or third-party servers and present them as client data.
  Technical tool documentation may be consulted to operate those tools.

The EP 4.5 label and Rebirth Evolution branding identify the test installation;
they do not prove uniformity across all clients of that episode. Every
conclusion must identify the analyzed client hash.

Server-only rules may be absent: drop rates, respawn, some formulas, and
validation rules, for example. Mark unsupported conclusions as `unknown`.
During phase B, document any policy we choose as an implementation decision,
without attributing it to the original server. Complete compatibility means
covering this client's observable contract and behavior, not recovering
internal rules that it does not reveal.

## Initial state to preserve

- Fork: `https://github.com/dsatin/Imgeneus`.
- Working branch: `develop/ep45-compatibility` and derived branches.
- Linux base: `63e0248ab148481dabe8394a34edd06720525b09`.
  Original upstream: `0ce355594d521c3a06a08f24d0a9b60ebc8a459f`.
- The existing backend targets EP8. Its serializers, limits, seeds, and
  rules are reuse candidates subject to comparison with the target client.
- Login, character creation, first map entry, and logout were observed.
  The second entry after logout failed.
- The snapshot includes an additional character-selection packet change
  that has not been compiled or validated. Do not report it as a completed fix.
- Do not reset databases, volumes, or accounts for the inventory. Keep the
  server as a test bench during phase A; limit server changes to instrumentation
  required to collect evidence.

Local reference client:

```text
/home/dsatin/Games/Heroic/Prefixes/Shaiya EP 4.5/drive_c/RebirthEvolution
```

Accept its path through parameters or local configuration. Do not make this
specific path a required tool dependency. Known hashes and the local IP patch
are recorded in `docs/client-ep45/baseline.md`.

## Reference organization

Keep durable specifications in `docs/client-ep45/`:

| Path | Contents |
| --- | --- |
| `README.md` | Index, conventions, reproduction instructions |
| `progress.md` | Active phase, tasks, exit criteria, pending work |
| `baseline.md` | Analyzed version, hashes, environment, snapshot limits |
| `catalogs/` | File manifests and normalized JSON/CSV tables |
| `schemas/` | Data/evidence schemas and binary formats |
| `domains/` | Items, skills, mobs, NPCs, maps, and additional domains |
| `ui/` | Screens, controls, states, strings, resources, interaction flows |
| `protocol/` | C→S/S→C packets, encryption, state machines |
| `analysis/` | Executable analysis, functions, offsets, hypotheses |
| `validation/` | Integrity, coverage, and test-session reports |
| `backend/` | Derived requirements, gaps, phase B dependencies |
| `templates/` | Uniform domain documentation template |

Implement reproducible tools in `tools/ep45-client/`. Reserve
`.client-ep45-cache/` for originals, extracted files, full disassembly, dumps,
captures, and large exports. Exclude it from Git and the Docker context.
Version manifests, schemas, documentation, scripts, and small sanitized
evidence. Never commit `game.exe`, `data.saf`, memory dumps, credentials,
or local settings. Index large exports by path, count, and hash.

### Evidence standard

Each record, field, format, flow, or requirement must identify:

1. A stable ID and domain; preserve original client IDs without renumbering.
2. Baseline hash and source path; offset/length where applicable.
3. Tool version/commit, parameters, reproduction command, and observation date.
4. Original values, normalized representation, and relationships by ID.
5. Status: `inventoried`, `extracted`, `decoded`, `statically_validated`,
   `runtime_validated`, `inferred`, `unknown`, or `not_applicable_with_evidence`.
6. Validation method, verifiable evidence, unknown fields, and backend
   implications. Label hypotheses explicitly.

Report extracted file counts, decoded format counts, cataloged entity counts,
and validated interaction counts separately. They measure different coverage.

## Phase A — extract and document the client

### A0. Freeze and identify the sample

1. Record project/submodule commits, OS, Wine/Proton, launch arguments,
   ports, and relevant settings without secrets.
2. Recursively inventory loose files and stream SHA-256, including executables,
   DLLs, INIs, and SAH/SAF. Preserve original dates.
3. Record original and locally patched executables separately, changed bytes,
   and patch purpose. Analyze copies; open client sources read-only.
4. Record size, PE timestamp, architecture, language, and declared versions.
   Do not infer the episode from a directory name or INI.
5. Document reproduction of observed login/first entry and failed reentry.

Deliver an external manifest, identified baseline, and explicit historical
test list. The external manifest is not the SAF's internal inventory.

### A1. Index and extract the entire data archive

1. Read SAH without modifying SAF. Record signature, version, declared count,
   full tree, original/normalized paths, ordinals, offsets, lengths, and duplicates.
2. Check counts, interval bounds/overlaps, path collisions, and case collisions.
   Preserve duplicates; do not lose entries through dictionary replacement.
3. Extract to cache with the tree intact. Reject absolute and traversal paths.
   Identical filenames may belong to different domains; do not flatten folders.
4. Read in blocks, verify actual byte counts, hash each content, and compare
   extracted files with the original SAF interval.
5. Report directory, extension, actual signature, and size distributions.
   Classify every entry, including extensionless and unidentified files.
6. Record errors per entry and support resume. Parser failures remain in
   report denominators and must not disappear silently.

Parsec provides `Data.FileIndex`, `GetFileBuffer`, and `ExtractAll`; verify
path preservation, duplicates, and error handling before reuse. `Episode.EP4`
is not proof of EP 4.5 support: `Item.Type` currently falls back to the EP5
reader. Validate the actual bytes.

Deliver `archive-files.jsonl`, count summaries, content hashes, an extraction
manifest, and an opaque-file report. Large manifests may remain in cache
with a versioned index and hash.

### A2. Discover formats and implement readers

1. Group samples by signature/structure, not extension alone.
2. Determine SData/table encryption, compression, headers, endianness, encoding,
   counts, fixed/variable lengths, and sentinels.
3. Compare Parsec readers and confirm fields against bytes and client loading
   routines. Implement project adapters; keep any submodule changes explicit
   and reproducible.
4. Preserve unknown field bytes and offsets. Do not skip extra bytes just to
   make a parser succeed or assign arbitrary semantic names.
5. Export raw and normalized representations with schemas, IDs, units, enums,
   and relationships. JSON/JSONL is authoritative; CSV must preserve lists
   and relationships if provided as a tabular view.
6. Validate first/last records, complete consumption, counts, extreme values,
   references, and samples of every variant. Where suitable, verify
   read→write→read using cache copies.
7. Test truncation, invalid counts, and layout variants. Pin tool versions
   and produce deterministic structured content.

Deliver per-format schemas, reproducible readers, field catalogs, small
fixtures, and decoding reports.

### A3. Catalog every content domain

Investigate these groups and every additional group discovered in the index.
Candidate filenames must be verified in the sample before claiming presence.

| Domain | Data and relationships |
| --- | --- |
| Characters | Factions, races, classes, modes, sex, hair/face/height, slots, animations, models, visible progression, limits |
| Items | `(type,typeId)`, names/descriptions, categories, icons/models, slots, requirements, stats, stacks, use, gems, craft, enchant, durability where present |
| Skills/buffs | IDs/levels, text/icons, targets, costs, range, timings, effects, requirements, relationships, quickbar representation |
| Mobs | IDs/text, appearance, animations/audio, available level/stat/AI indicators; distinguish appearance from authoritative rules |
| NPCs | IDs/types, faction, appearance, dialogue, shops/services, teleports, quest links |
| Quests | IDs/text, stages, prerequisites, objectives, NPC/mob/item links, displayed rewards, tracking flags |
| Maps | IDs/names, dimensions, origins/axes/units, terrain/collision, regions, water/sky/music, objects, visible access conditions |
| Map entities | Included positions, portals/destinations, NPCs, mobs/spawns, areas; do not invent missing SVMAP files |
| Economy | Shops, displayed prices, currency, trade, bank/warehouse, mail, auction, cash shop only where identified |
| Social/PvP | Chat, friends, party/raid, guilds, duels, ranks, kills, blessing, wars/events, screens/states |
| Visual assets | Textures, models, skeletons, effects, animations, clothing, weapons, mounts, emblems, entity links |
| UI/language | Layouts, panels, icons, tooltips, fonts, strings/errors, translations, keys/controls |
| Audio | Music, ambient/effect/voice audio, map/action/entity links |
| Configuration/extras | Networking, resolution/options, updater, auxiliary files, newly discovered categories |

For each domain produce a catalog, field dictionary, cross-references,
integrity report, and missing-information list. Mark absence only with
analysis evidence, never because the existing server lacks support.
Use `templates/domain.md`.

### A4. Map the UI and all exposed actions

1. Catalog UI resources/strings and executable panel references, including
   screens that cannot currently be opened.
2. Record each screen's entry/exit, buttons/shortcuts, states, apparent
   permissions/requirements, resource IDs, and messages.
3. Build the complete navigation tree and an action table:
   `action → initial state → local effect/packet → expected response → final state`.
4. Distinguish local actions from server-dependent actions. Record controlled
   tests/screenshots where useful; list inaccessible screens and known resources.
5. Include login, server/faction choice, character create/select/delete/rename,
   entry/logout/reentry, inventory/equipment, skills, NPCs, combat, quests,
   chat/social, shops, and every additional feature discovered.
6. Exercise success, cancellation, errors, limits, and repeated transitions.

Deliver screen/action indexes, flows, a UI/data/packet matrix, and visible
features requiring backend responses.

### A5. Map the protocol through the executable

1. Identify PE sections/imports, strings/xrefs, dispatch tables, socket routines,
   C→S builders, and S→C readers. Record RVA, file offset, and image base;
   distinguish virtual addresses from file offsets.
2. Enumerate opcodes in both directions. The EP8 `PacketType` enum is not
   necessarily this client's complete opcode catalog.
3. Record direction/opcode, sending/acceptance conditions, fields/types/lengths,
   order, encoding, counts, alignment, flags, variants, examples, and routines.
4. Document framing, maximum length, Login/World connections, addresses,
   handshake, key derivation, AES/XOR, and exact transition conditions.
5. Model authentication, selection, world, logout, return to selection,
   reentry, disconnection/reconnection, and retained/cleared client caches.
6. Link packet UI effects to catalog IDs/enums/limits. Use `unknown_*` fields
   for unresolved bytes.
7. Document the client's own optional features/variants and conditions;
   do not mix layouts from other episodes.

Deliver C→S/S→C opcode catalogs, binary specifications, function maps, and
state machines, including cases unreachable on the current server.

### A6. Validate runtime behavior

1. Capture only controlled test connections and link each session to the
   baseline, configuration, and scenario.
2. For encrypted traffic, observe buffers after decryption and before
   encryption through instrumentation/debugging. Encrypted PCAP alone
   cannot validate field layouts.
3. Correlate UI actions, packet ordering, states, and results. Separate what
   the client sent, what the bench returned, and what the client accepted.
   Our response is not proof of original server behavior.
4. Use minimal responses with documented layouts to expose screens.
   Isolated simulators/instrumentation are allowed, not gameplay implementation.
5. Validate repeated session cycles first: login→selection→map→logout→selection
   →same/different character, disconnect/reconnect, and client restart.
   Then exercise each domain's flows.
6. Record limits/counts, optional fields, rejections/errors/crashes, addresses,
   scenarios, and hypotheses. Absence of a crash does not prove a hypothesis.
7. Store raw captures/dumps in cache. Publish sanitized evidence only,
   without passwords, tokens, or real session key material.

Deliver sanitized fixtures, scenario traces, static/runtime comparisons,
and interaction coverage. Unreachable feature gaps need explicit static
contracts and planned tests.

### A7. Consolidate the specification and release phase B

Phase A ends only when `validation/phase-a-report.md` demonstrates:

- Every loose file and SAH/SAF entry is inventoried/classified with an extraction
  outcome. Counts/hashes reconcile; failures remain in denominators.
- All backend-required data formats are decoded with validated schemas and
  relationships. Other opaque assets remain cataloged with reasons/pending work.
- Every discovered domain/screen/action has a reference, status, and evidence.
  A fixed feature list must not hide new discoveries.
- Every discovered opcode/builder/reader has an entry, direction, layout or
  explicit gap. Required session/domain contracts have no blocking binary gaps.
- Every interaction has coverage and planned tests. Basic session cycles were
  analyzed at runtime; pending validations are separate with justification.
- Unavailable client data and required backend decisions are recorded.
  No EP8 rule has been treated as target-client evidence.
- Tools/commands reproduce manifests/catalogs/reports from the identified
  sample. Backend requirements cite evidence and have ordered dependencies.

Do not demand recovery of data demonstrably absent from the client, or claim
completion while required formats remain unreadable. Return to extraction
or analysis for blocking gaps. Record completed criteria and switch progress
to B without requiring informal approval for this already authorized plan.

## Phase B — implement from the reference

Start only after A7. Each change must cite specification IDs, provide
observable acceptance criteria, and update compatibility coverage. Similarity
alone does not justify copying an EP8 serializer.

1. **B0 — profile and boundaries:** isolate EP4.5 data/protocol from EP8;
   define interfaces, catalog versions, storage, configuration, and tests.
   Avoid historical flags scattered across gameplay rules.
2. **B1 — databases/importers:** derive account/character/definition schemas
   from catalogs; preserve IDs; implement migrations, idempotent import,
   referential integrity, and definition/player-state separation. Existing
   seeds are not authoritative. Test with isolated databases.
3. **B2 — networking/session:** framing, encryption, authentication, World
   announcement, faction/characters, initial sync, heartbeat, logout/reentry,
   reconnection, cleanup. Cover repeated cycles before expanding gameplay.
4. **B3 — world:** maps/coordinates, specified collision, presence/visibility,
   movement, portals, NPCs/mobs. Import spawns only from extracted data;
   document our own decisions separately.
5. **B4 — character/inventory:** stats/progression, equipment/items, gems,
   craft/enchant, durability, consumables, bank/warehouse, persistence,
   following identified formats and limits.
6. **B5 — combat/PvE:** skills/buffs, targets, damage/costs/timings, AI,
   death/revival, quests/rewards/drops. Separate client parameters from
   authoritative policies chosen to fill unavailable rules.
7. **B6 — economy/social/PvP:** shops/trade and other discovered commerce,
   chat/friends, party/raid, guilds, duels/ranks, blessing/events, following
   dependencies and actual client features.
8. **B7 — full compatibility:** exercise every matrix action, new features,
   errors/cancellation/limits, two or more connections, persistence, and
   prolonged sessions. Desynchronization and crashes are compatibility failures.
9. **B8 — delivery:** document Linux setup, client profile, migrations/import,
   operations, and final coverage. Publish limitations. Claim completion
   only with covered observable behavior and documented/tested policy decisions.

Validate binary layouts with extracted fixtures, session transitions,
persistence, isolated integration, and the actual client. Compare EP8 too
when common infrastructure is affected.

## Execution and delivery discipline

- The initial snapshot and plan are committed. Execute the current phase A
  task and update progress; never fill catalogs with fictional records.
- Keep changes focused by format/domain. Record commands, counts, uncertainty,
  and next steps. Use `rg` for searches.
- Keep secrets in `.env` and ignored local files. Extraction tools must work
  without database credentials or Internet access.
- Never overwrite the client, database, or raw reference files. Write new
  outputs in separate directories and verify integrity.
- Test according to risk: extraction integrity, parser bounds, binary contracts,
  and state transitions matter more than tests that mirror implementation.
- This plan does not request parallel agents or extra approval for reversible
  work. Respect the environment's effective permissions.
