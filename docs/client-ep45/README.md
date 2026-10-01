# Referência do cliente EP 4.5

Este diretório será a fonte de especificação para a compatibilidade com o
cliente Rebirth Evolution instalado para teste. A extração integral ainda
não começou. A identificação da amostra e algumas evidências das sessões
anteriores já estão registradas; nenhuma tabela de gameplay foi importada
como se fosse do EP 4.5.

O plano detalhado e a ordem do trabalho estão no [AGENTS.md](../../AGENTS.md).
Primeiro extrair e documentar o cliente; depois implementar o backend.

| Referência | Uso |
| --- | --- |
| [Progresso](progress.md) | Etapa ativa, tarefas e condições de passagem |
| [Baseline](baseline.md) | Cliente identificado e estado do snapshot |
| [Catálogos](catalogs/README.md) | Manifestos e formato das exportações |
| [Domínios](domains/README.md) | Escopo dos dados e relações a extrair |
| [Interface](ui/README.md) | Telas e matriz de ações |
| [Protocolo](protocol/README.md) | Descobertas atuais e contratos a mapear |
| [Análise](analysis/README.md) | Âncoras do executável e reprodução |
| [Validação](validation/README.md) | Integridade, cobertura e critérios de saída |
| [Backend](backend/README.md) | Requisitos derivados e sequência posterior |
| [Modelo de domínio](templates/domain.md) | Padrão de documentação |
| [Schema de evidência](schemas/provenance.schema.json) | Rastreabilidade de cada descoberta |

Os arquivos brutos e exportações volumosas ficam em `.client-ep45-cache/`,
fora do Git. As futuras ferramentas ficam em `tools/ep45-client/` e devem
receber o caminho do cliente como parâmetro. O manifesto inicial de arquivos
soltos é separado do futuro índice interno SAH/SAF.

Um dado só recebe status de validação em execução quando houver cenário e
resultado registrados. Uma descoberta estática não prova uma regra do
servidor original. Lacunas documentadas são parte da referência.
