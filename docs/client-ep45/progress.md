# Progresso e próxima execução

Etapa ativa: **A — extração e documentação**. Data do snapshot: 2026-10-01.
A implementação do backend da etapa B ainda não foi iniciada sob este plano.
As adaptações experimentais anteriores permanecem no snapshot histórico.

| ID | Trabalho | Estado | Próxima entrega |
| --- | --- | --- | --- |
| A0 | Identificação da amostra | Parcial | Manifesto externo completo, ferramentas/ambiente e reprodução das sessões |
| A1 | Índice e extração SAH/SAF | Pendente | Todas as entradas, hashes, árvore e relatório de integridade |
| A2 | Formatos e parsers | Pendente | Schemas, leitores e testes de integridade |
| A3 | Catálogos de conteúdo | Pendente | Todos os domínios com referências e lacunas |
| A4 | Interface e ações | Pendente | Índice de telas e matriz de interações |
| A5 | Protocolo estático | Parcial | Alguns leitores identificados; enumerar todas as direções/opcodes |
| A6 | Validação em execução | Parcial | Primeiro ciclo observado; reentrada e demais fluxos pendentes |
| A7 | Consolidação e critérios de saída | Pendente | `validation/phase-a-report.md` |
| B0–B8 | Implementação do backend | Aguardando A7 | Requisitos rastreáveis e execução por dependências |

## Primeira tarefa de extração

1. Concluir A0 e conferir o hash do cliente contra a baseline.
2. Implementar uma ferramenta que **liste** o SAH e valide offsets/contagens
   antes de extrair. Não presumir que o enum EP4 do Parsec seleciona um
   leitor próprio para esse cliente.
3. Extrair para cache preservando a árvore, conferindo bytes e gerando hashes.
4. Publicar o índice de todos os arquivos internos e a distribuição por
   domínio/formato, sem começar a implementar gameplay.

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
