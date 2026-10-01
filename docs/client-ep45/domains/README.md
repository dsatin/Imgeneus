# Domínios a extrair

Nenhum dos catálogos de gameplay abaixo foi extraído integralmente nesta
solicitação. Usar o [modelo](../templates/domain.md) para documentá-los.

| Grupo | Referência esperada | Relações principais |
| --- | --- | --- |
| Personagens | `characters.md` | Facção/raça/classe/modo, aparência, recursos e limites |
| Itens | `items.md` | `(type,typeId)`, requisitos, equipamentos, ícones/modelos, gemas e efeitos |
| Skills/buffs | `skills.md` | ID/nível, classe, custos, alvos, textos, efeitos e quickbar |
| Mobs | `mobs.md` | ID, texto, modelo/animação/áudio, mapas e dados disponíveis |
| NPCs | `npcs.md` | ID, tipo, facção, diálogo, loja/serviço, quest e mapa |
| Quests | `quests.md` | Etapas, objetivos, NPCs/mobs/itens e recompensas exibidas |
| Mapas | `maps.md` | ID, coordenadas, terreno/colisão, portais e posicionamentos incluídos |
| Economia | `economy.md` | Moedas, compras/vendas, trocas, armazenamento e sistemas encontrados |
| Social/PvP | `social-pvp.md` | Chat, amigos, grupos/guildas, duelo, ranks e eventos presentes |
| Recursos | `assets.md` | Texturas, modelos, animações, efeitos, fontes e áudio |
| Configuração | `configuration.md` | Rede, opções, updater, limites e arquivos auxiliares |

Essa lista é um ponto de partida, não um limite do inventário. Recursos
ausentes, opacos e desconhecidos continuam registrados com evidência.
Dados de servidor que não estejam no cliente devem gerar lacunas explícitas,
especialmente spawns, respawn, loot e fórmulas autoritativas.
