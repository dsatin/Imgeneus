# Interface e matriz de ações

Inventariar telas acessíveis e telas referenciadas por recursos/funções que
ainda não conseguimos abrir. Registrar IDs de imagens/textos, atalhos,
controle acionado, estado inicial/final e condições de acesso.

Formato da matriz futura em `actions.csv`:

```text
action_id,screen_id,control_id,initial_state,local_effect,c2s_opcodes,s2c_opcodes,final_state,evidence_id,status,backend_requirement
```

Listas de opcodes em uma célula precisam de uma convenção documentada.
Uma ação local deve indicar isso; uma ação não validada deve permanecer
pendente, mesmo que os recursos gráficos tenham sido extraídos.

Primeiro documentar a navegação de autenticação/seleção/mundo/logout e a
reentrada. Expandir para todos os painéis e menus encontrados no inventário:
inventário, equipamento, skills, NPCs/quests, lojas, chat, social/PvP,
configurações e recursos adicionais.

Cada fluxo deve incluir sucesso, cancelamento, erro e repetição. Screenshots
e registros devem apontar para a baseline e evitar dados de conta. Relacionar
interface aos catálogos e ao contrato de protocolo; aparência não comprova
implementação da regra de servidor.
