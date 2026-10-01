# Relatório A0/A1 — identificação e extração

Execução em 2026-10-01, projeto na base `eacfc1d6`, Python 3.14.7,
baseline `rebirth-evolution-ep45-98c7dd3a`. O backend e os bancos não foram
alterados por este trabalho.

## Resultados

| Indicador | Resultado |
| --- | --- |
| Arquivos externos congelados | 18 + executável original pré-patch |
| Entradas declaradas/lidas na árvore SAH | 23.564 / 23.564 |
| Pastas da árvore | 172 |
| Caminhos únicos da árvore | 23.563 |
| Entradas suplementares após a árvore | 6 |
| Entradas extraídas e verificadas | 23.570 |
| Bytes das entradas da árvore | 2.385.899.048 |
| Erros de extração/limites/path | 0 |
| Sobreposições entre intervalos da árvore | 0 |
| Duplicatas de caminho | 1, dois conteúdos idênticos preservados |
| Testes automatizados | 13 passaram |
| Registros de gameplay decodificados | 0 |

A extração existente foi conferida em uma segunda execução usando
`originals/` como fonte. Os arquivos brutos existentes foram mantidos;
cada hash de saída foi comparado novamente com a respectiva faixa no SAF.
Hashes completos do SAH/SAF foram reconferidos antes e depois das execuções.

## Saídas e reprodução

- [Identificação/PE/runner](../catalogs/baseline-evidence.json).
- [Manifesto externo atual](../catalogs/loose-files.current.json), preservando
  também o manifesto anterior. Só o hash de `CONFIG.INI` mudou.
- [Relatório de extração](../catalogs/extraction-report.json): hashes do
  cliente/ferramenta, contagens, classificações, validações e hash do índice.
- [Fontes de dados](../catalogs/data-sources.json),
  [arquivos de mapas](../catalogs/map-files.json) e
  [recursos/anomalias](../catalogs/asset-summary.json).
- Índice completo no cache: `archive-files.jsonl`, 23.570 registros,
  SHA-256 `09240d9b290aded79f66f40991e62cca19aca5eab90792d1f1f8b584fe847a29`.
- [Comandos e testes](../../../tools/ep45-client/README.md).

## Conteúdo identificado, ainda não decodificado

Há nove SData ativos: Cash, KillStatus, Skill, Item, NpcSkill, Monster,
GuildHouse, PriestTalk e NpcQuest. Seis apresentam o cabeçalho associado a
SEED; seus tamanhos declarados/alinhamento foram catalogados, mas a
descriptografia e o checksum ainda não foram validados.

Foram encontrados 86 WLD e um ZON, sem entradas `.svmap` no índice desta
amostra. Isso não prova ausência de informações de posicionamento nos
outros formatos. IDs obtidos de nomes de WLD são apenas candidatos.

A classificação por caminho identifica 997 recursos de UI e 1.039 arquivos
de áudio. São contagens de arquivos; telas, controles e interações ainda
não foram enumerados. Os 24 `Thumbs.db` têm assinatura de compound file e
foram separados dos candidatos a tabelas de gameplay. Dez arquivos `.dds`
começam com assinatura BMP; usar conteúdo e estrutura para selecionar leitores.

## Limites e próxima etapa

A0/A1 estão concluídas para identificação, inventário e extração das entradas
indexadas. A semântica dos seis registros suplementares e dos intervalos
não referenciados permanece desconhecida, com bytes preservados no SAF
congelado. Nenhuma regra autoritativa ou tabela de outro episódio foi importada.

A2 deve agora validar containers/descriptografia e layouts de registros,
seguida pelos catálogos de conteúdo, interface e protocolo. A etapa A não
está concluída como um todo; este relatório não libera a etapa B.
