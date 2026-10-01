# Implementação posterior à extração

Etapa B aguardando a conclusão documentada de A7. O código experimental
preservado nesta branch serve como histórico/bancada e não altera essa ordem.

Cada requisito futuro deve ter ID, domínio, fontes do cliente, contratos
de dados e pacotes, precondições, comportamento observável, persistência,
cenários de teste e status. Lacunas devem identificar se o cliente não
possui a informação ou se a extração ainda não a revelou.

| Ordem | Entrega | Dependência |
| --- | --- | --- |
| B0 | Perfil EP4.5 e fronteiras com EP8 | Especificação consolidada |
| B1 | Schema, migrações e importadores dos catálogos | IDs e relações extraídos |
| B2 | Login/World, personagens e ciclos de sessão | Protocolo e estados validados |
| B3 | Mapas, presença, movimento e entidades | Catálogos de mapas/recursos/entidades |
| B4 | Atributos, itens/equipamento e armazenamento | Itens, slots, limites e formatos |
| B5 | Skills/buffs, combate, PvE e quests | Dados e decisões documentadas para lacunas |
| B6 | Economia, social e PvP | Fluxos e sistemas presentes no cliente |
| B7 | Matriz integral e testes repetidos | Todos os recursos encontrados |
| B8 | Operação Linux e entrega | Cobertura demonstrada e limitações publicadas |

A base existente divide rede/criptografia em `Imgeneus.Network`, persistência
em `Imgeneus.Database`, definições em `Imgeneus.GameDefinitions`, lógica em
`Imgeneus.Game` e handlers/serializers em `Imgeneus.World`/`Imgeneus.Login`.
Comparar esses módulos com as especificações; não tratar seus seeds ou
formatos EP8 como dados do cliente alvo.

Decisões de drop, respawn, AI ou fórmulas sem evidência no cliente devem
ficar em documentos próprios de políticas, com testes e configuração,
explicitamente separadas do catálogo extraído. Cobrir o comportamento
observável não significa recuperar o código do servidor original.
