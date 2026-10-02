# UI and action matrix

[Initial resource catalog](resources.md): 997 UI-path resources with source
hashes and bounded metadata. Screen/action/state coverage remains pending.

Inventory accessible screens and screens referenced by assets/functions
that remain inaccessible. Record image/text IDs, shortcuts, controls,
initial/final states, and access conditions.

Planned `actions.csv` columns:

```text
action_id,screen_id,control_id,initial_state,local_effect,c2s_opcodes,s2c_opcodes,final_state,evidence_id,status,backend_requirement
```

Document the convention for opcode lists in cells. Identify entirely local
actions explicitly. Extracted graphics alone do not validate an interaction.

Document authentication/selection/world/logout/reentry first, then every
panel/menu found: inventory/equipment, skills, NPCs/quests, shops, chat,
social/PvP, settings, and additional features.

Include success, cancellation, error, and repetition. Link screenshots/tests
to the baseline without account data. Connect UI to catalogs and protocol
contracts; appearance does not demonstrate a server rule.
