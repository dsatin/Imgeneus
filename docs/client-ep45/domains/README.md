# Content domains

A1 extracted source files; A2 fully decoded eight of nine active SData sources
structurally. Skill lacks six expected records. Field semantics remain pending. See
[data sources](../catalogs/data-sources.json), [maps](../catalogs/map-files.json),
and the [domain template](../templates/domain.md).

| Group | Planned reference | Relationships |
| --- | --- | --- |
| Characters | `characters.md` | Faction/race/class/mode, appearance, assets, limits |
| Items | [items.md](items.md) | `(type,typeId)`, requirements, equipment, icons/models, gems/effects |
| Skills/buffs | [skills.md](skills.md) | ID/level, class, costs/targets, text/effects, quickbar |
| Mobs | [mobs.md](mobs.md) | ID/text, models/animation/audio, maps, available data |
| NPCs | [npcs.md](npcs.md) | ID/type/faction, dialogue, shop/service, quest/map |
| Quests | [quests.md](quests.md) | Stages, objectives, NPC/mob/item links, displayed rewards |
| Maps | [maps.md](maps.md) | ID/coordinates, terrain/collision, included portals/positions |
| Economy | [economy.md](economy.md) | Currency, buying/selling/trade, storage, discovered systems |
| Social/PvP | [social-pvp.md](social-pvp.md) | Chat/friends, groups/guilds, duels/ranks, present events |
| Assets | [assets.md](assets.md) | Textures, models, animations, effects, fonts |
| Audio | [audio.md](audio.md) | Music/effect/voice sources, chunk metadata, pending action/entity links |
| Configuration | `configuration.md` | Networking, settings/updater, limits, auxiliary files |

This list starts the inventory; it does not limit it. Absent/opaque/unknown
resources need evidence. Server data absent from the client must remain an
explicit gap, particularly spawns, respawn, loot, and authoritative formulas.
