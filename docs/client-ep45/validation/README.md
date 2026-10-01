# Validação e critérios de saída

Relatar separadamente: arquivos inventariados, extraídos, formatos
decodificados, entidades catalogadas, telas/ações identificadas, opcodes
mapeados, cenários executados e cenários aceitos pelo cliente.
Cada percentual deve declarar seu denominador e incluir erros/pendências.

## Integridade da extração

- Reconciliar contagem declarada no SAH com todas as entradas efetivas.
- Validar limites de cada intervalo no SAF e tamanhos realmente lidos.
- Conferir hashes da amostra e dos arquivos extraídos, duplicatas e colisões.
- Validar contagens de registros, offsets, consumo dos arquivos e relações.
- Reproduzir as saídas com as mesmas ferramentas e parâmetros.

## Cobertura de comportamento

Criar `compatibility-matrix.csv` com recurso/ação, especificação de dados/UI/
protocolo, evidência, implementação, cenário e resultado. Hoje a primeira
entrada e o logout foram observados; a reentrada falhou e os demais sistemas
não foram validados integralmente.

Os cenários básicos devem incluir mesma e outra personagem após logout,
logout repetido, desconexão/reconexão e reinício do cliente. Depois cobrir
ações de inventário, equipamentos, NPCs/portais, combate/skills/quests,
economia/social/PvP e todos os recursos adicionais encontrados.

## Passagem para implementação

O futuro `phase-a-report.md` deve demonstrar cada critério A7 do AGENTS.md,
listar lacunas bloqueantes e distinguir informações que o cliente não
contém. Não iniciar B com um formato necessário ainda desconhecido. Não
exigir recuperar dados de servidor ausentes da amostra; documentar essas
ausências e quais decisões próprias serão necessárias.

O novo writer de seleção não tem resultado de build ou runtime no snapshot.
Os checks anteriores do inventário/desconexão passaram em uma imagem
anterior; isso não valida automaticamente o código adicional preparado.
