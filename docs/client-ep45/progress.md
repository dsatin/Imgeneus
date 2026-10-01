# Progresso e próxima execução

Etapa ativa: **A — extração e documentação**. Data do snapshot: 2026-10-01.
A implementação do backend da etapa B ainda não foi iniciada sob este plano.
As adaptações experimentais anteriores permanecem no snapshot histórico.

| ID | Trabalho | Estado | Próxima entrega |
| --- | --- | --- | --- |
| A0 | Identificação da amostra | Concluída | 18 arquivos congelados + executável original; PE, hashes, ambiente e alteração do IP conferidos |
| A1 | Índice e extração SAH/SAF | Concluída | 23.564 entradas da árvore + 6 suplementares, hashes e retomada verificados; zero erros |
| A2 | Formatos e parsers | Em andamento | Cabeçalhos e candidatos catalogados; descriptografia e registros ainda pendentes |
| A3 | Catálogos de conteúdo | Pendente | Todos os domínios com referências e lacunas |
| A4 | Interface e ações | Pendente | Índice de telas e matriz de interações |
| A5 | Protocolo estático | Parcial | Alguns leitores identificados; enumerar todas as direções/opcodes |
| A6 | Validação em execução | Parcial | Primeiro ciclo observado; reentrada e demais fluxos pendentes |
| A7 | Consolidação e critérios de saída | Pendente | `validation/phase-a-report.md` |
| B0–B8 | Implementação do backend | Aguardando A7 | Requisitos rastreáveis e execução por dependências |

## Resultados de A0/A1

Ver [relatório](validation/phase-a0-a1.md),
[comandos](../../tools/ep45-client/README.md) e
[fontes de dados](catalogs/data-sources.json).

- Árvore de 172 pastas; 23.564 entradas e 23.563 caminhos únicos.
- Um caminho duplicado, conteúdos idênticos, ambas as entradas preservadas.
- Seis registros adicionais no fim do SAH, sem semântica confirmada.
- Manifesto completo de 23.570 registros no cache; resumo e hash versionados.
- Nove SData ativos, seis com cabeçalho SEED; 86 WLD e um ZON.
- 24 `Thumbs.db` separados das fontes de gameplay; dez DDS com assinatura BMP.
- Conteúdo não referenciado pelo índice registrado; SAF completo preservado.
- 13 testes de integridade/retomada/contenção passaram. Uma segunda execução
  verificou a extração existente usando a cópia congelada como fonte.

## Próxima tarefa: A2

1. Confirmar o formato dos seis containers SEED com análise do cliente,
   validar descriptografia/checksum e preservar os bytes originais.
2. Decodificar os nove SData, começando por itens, skills, mobs e NPCs/quests,
   validando tamanhos, contagens e referências. Não usar o fallback EP5 como
   prova de layout EP4.5.
3. Documentar os formatos de WLD/ZON, recursos e interface; os IDs numéricos
   dos nomes de WLD ainda são candidatos, não entidades confirmadas.
4. Produzir catálogos de registros com schemas e evidências. A contagem atual
   de registros de gameplay decodificados permanece zero.

## Pendências herdadas do experimento

- Segunda entrada após logout: o servidor enviou logout/lista/facção e não
  recebeu nova seleção na sessão observada. Causa ainda não confirmada.
- Writer experimental de seleção de personagens: alteração de código
  preparada; build e execução ainda não realizados. Não atribuir ao patch
  um resultado de cliente que não aconteceu.
- Inventário inicial adaptado; movimentação de itens e outros pacotes ainda
  usam formatos herdados que exigem comparação.
- Leitor da barra de atalhos do cliente e estrutura do servidor aparentam
  diferenças. Documentar builders e readers antes de corrigir.
- Dados e seeds existentes do servidor não foram extraídos desta amostra.

## Como atualizar

Para cada tarefa concluída registrar arquivos de saída, contagens e fonte
de evidência, comando reexecutável, limitações e próximo passo. Manter
separados inventário, extração, decodificação e validação em execução.
A mudança para B ocorre quando o relatório de A7 cumprir os critérios do
AGENTS.md, e deve ser registrada aqui com os links das evidências.
