# Imgeneus: compatibilidade com o cliente EP 4.5

## Objetivo e ordem obrigatória do trabalho

Construir um backend compatível com o cliente EP 4.5 instalado localmente,
usando exclusivamente esse cliente como fonte de especificação. Primeiro
inventariar, extrair, analisar e documentar o que o cliente contém e espera.
Somente depois da conclusão verificável dessa etapa iniciar a implementação
do backend. O plano abrange dados, interface, recursos gráficos/sonoros,
protocolo e estados da sessão; entrar no mapa não significa compatibilidade
completa.

Antes de trabalhar, ler `docs/client-ep45/README.md`, `progress.md`,
`baseline.md` e as referências do domínio afetado. Atualizar o progresso e
registrar evidências ao concluir cada tarefa. A etapa ativa consta de
`docs/client-ep45/progress.md`; atualmente é **A — extração e documentação**.

### O que conta como fonte

- Executável, DLLs, arquivos soltos, arquivos internos de `data.sah/data.saf`,
  textos, imagens, sons, interface e comportamento do cliente alvo.
- Análise estática, depuração e tráfego do próprio cliente em testes com
  nosso servidor ou uma bancada local. Uma captura após descriptografia
  também é evidência do cliente.
- Parsec, ferramentas de análise e o código existente podem servir de
  infraestrutura. Não são prova de que um formato ou regra é EP 4.5.
- Pacotes, SQL, dados, fórmulas ou documentação de outros episódios e de
  servidores de terceiros não devem preencher lacunas como se fossem dados
  extraídos desse cliente. Documentação técnica de ferramentas pode ser
  consultada para utilizá-las.

O rótulo "EP 4.5" e a marca Rebirth Evolution identificam a instalação de
teste, mas não provam uniformidade com todos os clientes desse episódio.
Toda conclusão deve identificar o hash do cliente analisado.

Regras exclusivas do servidor podem não estar presentes no cliente: por
exemplo, taxas de drop, respawn, algumas fórmulas e validações. Quando não
houver evidência, marcar como desconhecido. Na etapa B, uma política própria
deve ser documentada como decisão de implementação, sem atribuí-la ao
servidor original. Compatibilidade completa significa cobrir o contrato e
os comportamentos observáveis desse cliente; não prometer recuperar regras
internas que ele não revela.

## Estado inicial a preservar

- Fork: `https://github.com/dsatin/Imgeneus`.
- Trabalhar em `develop/ep45-compatibility` e branches derivadas. Preservar
  `master` e `develop/linux-server`; não fazer force push nem reescrever a
  base para esta iniciativa.
- Base Linux: `63e0248ab148481dabe8394a34edd06720525b09`; upstream original:
  `0ce355594d521c3a06a08f24d0a9b60ebc8a459f`.
- O backend existente nasceu para EP8. Seus serializers, limites, seeds e
  regras são candidatos a reutilização, sujeitos à comparação com EP 4.5.
- Login, criação de personagem, primeira entrada no mapa e logout já foram
  observados com o cliente EP 4.5. A segunda entrada após logout falhou.
- O snapshot inclui uma alteração adicional no pacote de seleção de
  personagens que ainda não foi compilada nem validada com o cliente.
  Não apresentá-la como correção concluída.
- Não reinicializar bancos, volumes ou contas para executar o inventário.
  Durante a etapa A, preservar o servidor como bancada; mudanças nele se
  limitam à instrumentação necessária para coletar evidências.

Cliente local de referência:

```text
/home/dsatin/Games/Heroic/Prefixes/Shaiya EP 4.5/drive_c/RebirthEvolution
```

Aceitar o caminho por parâmetro ou configuração local, sem torná-lo uma
dependência obrigatória das ferramentas. Os hashes conhecidos e a alteração
local do IP estão em `docs/client-ep45/baseline.md`.

## Organização da referência

Toda especificação duradoura fica em `docs/client-ep45/`:

| Caminho | Conteúdo esperado |
| --- | --- |
| `README.md` | Índice, convenções e instruções de reprodução |
| `progress.md` | Etapa ativa, tarefas, critérios de saída e pendências |
| `baseline.md` | Versão analisada, hashes, ambiente e limites do snapshot |
| `catalogs/` | Manifestos de arquivos e tabelas normalizadas em JSON/CSV |
| `schemas/` | Esquemas dos dados e das evidências; formatos binários |
| `domains/` | Referências de itens, skills, mobs, NPCs, mapas e outros domínios |
| `ui/` | Telas, controles, estados, textos, recursos e fluxos de interação |
| `protocol/` | Pacotes C→S/S→C, criptografia e máquinas de estados |
| `analysis/` | Análise do executável, funções, offsets e hipóteses |
| `validation/` | Relatórios de integridade, cobertura e sessões de teste |
| `backend/` | Requisitos derivados, lacunas e sequência da etapa B |
| `templates/` | Modelo uniforme para documentar cada domínio |

Criar ferramentas reproduzíveis em `tools/ep45-client/` quando começar a
extração. Reservar `.client-ep45-cache/` para originais, arquivos extraídos,
disassembly completo, dumps, capturas e exportações volumosas. Essa pasta
fica fora de Git e do contexto Docker. Versionar manifestos, schemas,
documentação, scripts e evidências pequenas e sanitizadas. Não commitar
`game.exe`, `data.saf`, dumps de memória, credenciais ou configurações locais.
Exportações enormes devem ter índice e hash na referência, sem inflar Git.

### Padrão de evidência

Cada registro, campo, formato, fluxo ou requisito deve conter:

1. ID estável e domínio; ID original do cliente, sem renumerá-lo.
2. Hash da baseline e caminho da fonte; offset/tamanho quando aplicável.
3. Ferramenta, versão/commit, parâmetros, comando de reprodução e data.
4. Valores originais, representação normalizada e relações por IDs.
5. Status: `inventariado`, `extraido`, `decodificado`,
   `validado_estaticamente`, `validado_em_execucao`, `inferido`,
   `desconhecido` ou `nao_aplicavel_com_evidencia`.
6. Método de validação, evidência verificável, campos desconhecidos e
   implicações para o backend. Hipóteses devem ser identificadas como tais.

Não confundir número de arquivos extraídos com número de formatos
decodificados, nem contagem de entidades com contagem de interações
validadas. Publicar esses indicadores separadamente.

## Etapa A — extrair e documentar o cliente

### A0. Congelar e identificar a amostra

1. Registrar commit do projeto, commits dos submódulos, SO, Wine/Proton,
   argumentos de execução, portas e configurações relevantes sem segredos.
2. Inventariar recursivamente os arquivos soltos e gerar SHA-256 em streaming,
   incluindo executáveis, DLLs, INIs e o par SAH/SAF. Preservar datas originais.
3. Registrar separadamente o executável original e o com IP local alterado,
   os bytes modificados e a finalidade do patch. Analisar uma cópia; abrir
   os arquivos do cliente somente para leitura.
4. Anotar tamanho, PE timestamp, arquitetura, idioma e números declarados
   de versão. Não inferir o episódio apenas do nome de uma pasta ou INI.
5. Documentar como reproduzir login e primeiro acesso já observados, e como
   reproduzir a falha da segunda entrada após logout.

Saída: manifesto externo, baseline identificada e lista explícita de testes
anteriores. O manifesto externo não representa o inventário interno do SAF.

### A1. Indexar e extrair todo o arquivo de dados

1. Ler o índice SAH sem alterar o SAF. Registrar assinatura, versão, contagem
   declarada, árvore completa e cada entrada: caminho original, caminho
   normalizado, ordinal, offset, tamanho, versão e duplicidades.
2. Conferir quantidade de entradas, limites de cada intervalo no SAF,
   intervalos sobrepostos e colisões de nomes/case. Preservar entradas
   duplicadas; não depender apenas de um dicionário que possa descartá-las.
3. Extrair cada entrada para cache preservando sua árvore. Rejeitar caminhos
   absolutos ou com travessia fora da pasta de saída. Não achatar pastas:
   arquivos com o mesmo nome podem pertencer a domínios distintos.
4. Ler por blocos/arquivos, conferir bytes realmente lidos, calcular hash de
   cada conteúdo e verificar o resultado extraído contra o intervalo no SAF.
5. Produzir distribuição por diretório, extensão, assinatura real e tamanho;
   classificar todos os arquivos, inclusive os sem extensão ou desconhecidos.
6. Registrar erros individualmente e permitir retomada. Uma falha de parser
   não pode desaparecer silenciosamente do relatório.

Parsec já oferece `Data.FileIndex`, `GetFileBuffer` e `ExtractAll`, mas é
necessário verificar preservação de caminhos, duplicatas e tratamento de
erros. O enum `Episode.EP4` não comprova suporte ao EP 4.5: na revisão atual,
`Item.Type` usa o leitor EP5 como fallback. Validar os bytes antes de usá-lo.

Saída: `catalogs/archive-files.jsonl`, resumo de contagens, hashes por arquivo,
manifesto da extração e relatório de arquivos ainda opacos.

### A2. Descobrir formatos e construir leitores

1. Agrupar amostras por assinatura/estrutura, não somente por extensão.
2. Para SData e tabelas, determinar criptografia/compressão, cabeçalhos,
   endianness, codificação, contagens, tamanhos fixos/variáveis e sentinelas.
3. Comparar com leitores do Parsec e confirmar cada campo contra os bytes e
   as rotinas de leitura do cliente. Criar adaptadores no projeto; manter
   modificações de submódulos explícitas e reproduzíveis quando necessárias.
4. Preservar offsets e bytes dos campos desconhecidos. Não consumir bytes
   extras apenas para fazer um parser "passar" nem atribuir nomes arbitrários.
5. Exportar uma representação bruta e outra normalizada, com esquema, IDs,
   unidades, enumerações e relações. JSON/JSONL é a fonte estruturada; CSV
   pode ser uma visão tabular, sem perda de listas e relações.
6. Validar registros iniciais/finais, consumo completo do arquivo, contagens,
   valores extremos, referências e amostras de cada variante. Para formatos
   adequados, conferir leitura→escrita→leitura em cópias no cache.
7. Cobrir truncamento, contagens inválidas e variações de layout com testes
   significativos. Fixar versão das ferramentas e garantir saída determinística.

Saída: schemas por formato, leitores reproduzíveis, catálogo de campos,
fixtures pequenas e relatórios de decodificação.

### A3. Catalogar todos os domínios de conteúdo

Investigar os grupos abaixo e tudo mais descoberto no índice. Os nomes de
arquivos são candidatos; verificar se existem nesta amostra antes de afirmar
que determinado recurso está presente.

| Domínio | Dados e relações a documentar |
| --- | --- |
| Personagens | Facções, raças, classes, modos, sexo, cabelo/rosto/altura, slots, animações, modelos, progressão visível e limites |
| Itens | Chave `(type,typeId)`, nomes, descrições, categorias, ícones, modelos, slots, requisitos, atributos, empilhamento, uso, gemas, craft, enchant e durabilidade quando presentes |
| Skills e buffs | IDs/níveis, textos, ícones, alvos, custos, alcance, tempos, efeitos, requisitos, relações e representação na barra de atalhos |
| Mobs | IDs, textos, aparência, animações, sons, indicadores de nível/atributos/AI quando presentes; separar aparência de regra autoritativa |
| NPCs | IDs, tipos, facção, aparência, diálogos, lojas, serviços, teleporte e vínculos com quests |
| Quests | IDs, textos, etapas, pré-requisitos, objetivos, NPCs/mobs/itens, recompensas exibidas e flags de acompanhamento |
| Mapas | IDs, nomes, dimensões, origem/eixos/unidades, terreno, colisão, regiões, água, céu, música, objetos e condições visíveis de acesso |
| Entidades dos mapas | Posicionamentos, portais, destinos, NPCs, mobs/spawns e áreas, quando efetivamente incluídos no cliente; não inventar SVMAP ausente |
| Economia | Lojas, preços visíveis, moeda, troca, banco, warehouse, correio, leilão e cash shop somente quando identificados |
| Social e PvP | Chat, amigos, party/raid, guilda, duelos, ranks, mortes, bênção, guerra/eventos e suas telas/estados |
| Recursos visuais | Texturas, modelos, esqueletos, efeitos, animações, vestimentas, armas, montarias, emblemas e ligações com entidades |
| Interface e idioma | Layouts, painéis, ícones, tooltips, fontes, strings, mensagens de erro, traduções, teclas e controles |
| Áudio | Música, ambiente, efeitos, vozes e seus vínculos com mapas/ações/entidades |
| Configuração e extras | Rede, resoluções, opções, updater, arquivos auxiliares e categorias novas encontradas |

Para cada domínio gerar catálogo, dicionário de campos, referências entre
entidades, relatório de integridade e lista de informações ausentes. Marcar
features ausentes como tal apenas com evidência da análise, nunca pela falta
de suporte no servidor atual. Usar `templates/domain.md`.

### A4. Mapear interface e todas as ações expostas

1. Catalogar recursos de UI e strings, identificando painéis também por
   referências do executável, não apenas pelas telas acessíveis hoje.
2. Para cada tela, registrar entrada/saída, botões, atalhos, estados,
   permissões/requisitos aparentes, IDs de recursos e mensagens.
3. Montar uma árvore de navegação completa e uma tabela
   `ação → estado inicial → efeito local/pacote → resposta esperada → estado final`.
4. Distinguir ações inteiramente locais de ações que dependem do servidor.
   Capturar screenshots e testes controlados quando úteis; registrar telas
   inacessíveis como pendência, com seus recursos/funções encontrados.
5. Incluir login, escolha de servidor/facção, criação/seleção/exclusão/rename,
   entrada, logout, reentrada, inventário/equipamento, skills, interação com
   NPC, combate, quests, chat/social, lojas e toda feature adicional encontrada.
6. Exercitar sucesso, cancelamento, erro, limites e transições repetidas.
   Não limitar o mapeamento ao caminho feliz.

Saída: índice de telas e ações, fluxos, matriz UI/dados/pacotes e lista de
features visíveis que exigem resposta do backend.

### A5. Mapear o protocolo pelo executável

1. Identificar seções PE, imports, strings, referências cruzadas, tabelas de
   dispatch, rotinas de socket, builders C→S e leitores S→C. Registrar RVA e
   offset de arquivo; distinguir endereço virtual de offset e anotar a base.
2. Enumerar os opcodes encontrados em ambas as direções. Não assumir que a
   enumeração `PacketType` do EP8 é a enumeração completa desse cliente.
3. Para cada pacote registrar direção, opcode, condição de envio/aceitação,
   campos, tipos/tamanhos, ordem, encoding, contagens, alinhamento, flags,
   variantes, exemplos e rotina responsável.
4. Documentar framing, tamanho máximo, conexões Login/World, endereços,
   handshake, derivação de chaves, AES/XOR e exata condição de cada transição.
5. Construir máquinas de estados para autenticação, seleção, mundo, logout,
   retorno à seleção, reentrada, desconexão e reconexão. Registrar quais
   estados e caches são mantidos ou limpos no cliente.
6. Marcar efeitos de pacotes sobre a UI e ligar o protocolo aos catálogos de
   IDs, enums e limites. Preservar desconhecidos como campos `unknown_*`.
7. Documentar recursos opcionais/variantes do próprio cliente com suas
   condições; não misturar layouts de outros episódios.

Saída: catálogo de opcodes C→S/S→C, especificações binárias, mapa de funções
e máquinas de estados. O inventário estático deve incluir casos não
alcançáveis no servidor atual.

### A6. Validar comportamento em execução

1. Usar o cliente com a bancada local. Capturar somente as conexões de teste;
   associar cada sessão à baseline, configuração e cenário executado.
2. Quando houver criptografia, observar os buffers após descriptografia e
   antes da criptografia por instrumentação/depuração. PCAP de bytes
   cifrados, isoladamente, não confirma o layout dos campos.
3. Correlacionar ação da UI, ordem dos pacotes, estados e resultado. Analisar
   separadamente o que o cliente enviou, o que a bancada respondeu e o que
   o cliente aceitou. Uma resposta nossa não prova comportamento original.
4. Usar respostas mínimas com layouts já documentados para tornar telas
   acessíveis. Instrumentação e simuladores isolados são permitidos nesta
   etapa; isso não antecipa a implementação das regras do backend.
5. Validar primeiro ciclos de sessão repetidos: login → seleção → mapa →
   logout → seleção → mesma/outra personagem; desconexão/reconexão; restart
   do cliente. Depois validar os fluxos de cada domínio.
6. Registrar limites, contagens, campos opcionais, rejeições, erros e crashes
   com endereço, cenário e hipótese. Nunca transformar uma hipótese em
   confirmação apenas porque o cliente não fechou.
7. Guardar capturas brutas/dumps no cache e publicar somente registros
   sanitizados, sem senhas, tokens ou material de chaves de sessões reais.

Saída: fixtures sanitizadas, rastros de cenários, comparação estático/runtime
e cobertura das interações. Lacunas que dependem de features ainda ausentes
devem ter contrato estático e teste previsto explicitamente documentados.

### A7. Consolidar a especificação e liberar a etapa B

A etapa A só termina quando houver relatório em
`validation/phase-a-report.md` comprovando:

- Todos os arquivos soltos e todas as entradas SAH/SAF estão inventariados,
  classificados e com resultado de extração registrado. Contagens e hashes
  reconciliados; falhas não desaparecem do denominador.
- Todos os formatos de dados necessários ao backend estão decodificados,
  com esquemas e relações validados. Recursos opacos sem relevância para o
  backend permanecem catalogados com motivo e pendência explícitos.
- Todos os domínios e todas as telas/ações encontrados possuem referência,
  status e evidência. Não usar uma lista fixa para ocultar novas descobertas.
- Todos os opcodes e builders/readers encontrados têm entrada, direção,
  layout ou pendência. Os contratos necessários à sessão e aos domínios
  implementáveis não podem ter lacunas binárias bloqueantes.
- Existe matriz de cobertura e testes previstos para cada interação. Os
  ciclos básicos de sessão foram analisados em execução; demais validações
  pendentes estão separadas das confirmações, com justificativa.
- Estão registrados os dados não disponíveis no cliente e as decisões que
  o backend precisará tomar; nenhuma regra EP8 foi tratada como evidência EP4.5.
- Ferramentas e comandos reproduzem manifestos, catálogos e relatórios a
  partir da amostra identificada. Requisitos do backend apontam para suas
  evidências e estão organizados em dependências.

Não exigir recuperar dados que o cliente comprovadamente não contém, nem
declarar o mapeamento completo com formatos necessários ainda ilegíveis.
Se aparecer uma lacuna bloqueante, voltar à tarefa de extração/análise
correspondente. Registrar a conclusão dos critérios e mudar a etapa ativa
para B; não depender de uma aprovação informal para executar o plano já
autorizado.

## Etapa B — implementar o backend a partir da referência

Somente depois de A7. Toda alteração deve citar IDs de especificações em
`docs/client-ep45/`, incluir critérios observáveis e atualizar a matriz de
compatibilidade. Não copiar um serializer EP8 apenas por semelhança.

1. **B0 — perfil e fronteiras:** separar dados e protocolo EP4.5 do legado
   EP8; definir interfaces, versionamento dos catálogos, armazenamento,
   configurações e testes. Evitar flags históricas espalhadas por regras.
2. **B1 — bancos e importadores:** derivar schema de contas/personagens e
   definições dos catálogos; manter IDs; criar migrações, importação idempotente,
   integridade referencial e separação entre definições e estado dos jogadores.
   Seeds existentes não são fonte de verdade. Testar em banco isolado.
3. **B2 — rede e sessão:** framing, criptografia, autenticação, anúncio de
   World, facção, personagens, sincronização inicial, heartbeat, logout,
   reentrada, reconexão e limpeza de recursos. Cobrir ciclos repetidos antes
   de ampliar gameplay.
4. **B3 — mundo:** mapas, coordenadas, colisão quando especificada, presença,
   visibilidade, movimentação, portais, NPCs e mobs. Importar spawns somente
   quando houver dados extraídos; decisões próprias ficam documentadas.
5. **B4 — personagem e inventário:** atributos/progressão, equipamentos,
   itens, gemas, craft/enchant, durabilidade, consumíveis, banco/warehouse e
   persistência, seguindo os formatos e limites identificados.
6. **B5 — combate e PvE:** skills/buffs, alvos, danos/custos/tempos, AI,
   morte/revive, quests, recompensas e drops. Separar parâmetros do cliente
   de políticas autoritativas escolhidas para preencher ausências.
7. **B6 — economia/social/PvP:** lojas/trocas, demais sistemas comerciais
   presentes, chat, amigos, party/raid, guilda, duelo, ranks, bênção e eventos,
   conforme dependências e recursos efetivamente encontrados.
8. **B7 — compatibilidade integral:** percorrer todas as ações da matriz,
   incluindo features adicionais descobertas, erros, cancelamentos, limites,
   duas ou mais conexões, persistência e sessões prolongadas. Tratar perdas
   de sincronismo e crashes como falhas de compatibilidade.
9. **B8 — entrega:** documentar instalação Linux, perfil do cliente,
   migrações/importação, operação e cobertura final. Publicar limitations
   explícitas; marcar completo apenas quando a matriz observável estiver
   coberta e as decisões de regras ausentes estiverem documentadas/testadas.

Validação: testes de layouts com fixtures extraídas, testes das transições e
da persistência, integração em ambiente isolado e cenários com o cliente
real. Comparar também com EP8 se uma mudança afetar infraestrutura comum.

## Disciplina de execução e entrega

- Nesta solicitação, criar o snapshot e o plano; a extração integral é o
  próximo trabalho. Não preencher catálogos com dados fictícios.
- Manter mudanças pequenas por formato/domínio. Registrar comandos,
  contagens, incertezas e próximos passos; usar buscas com `rg`.
- Manter segredos em `.env` e arquivos locais ignorados. As ferramentas de
  extração devem funcionar sem credenciais do banco ou acesso à Internet.
- Não sobrescrever cliente, banco ou arquivos de referência brutos. Produzir
  novas saídas em diretórios próprios e verificar integridade.
- Testar de acordo com o risco: integridade de extração, limites do parser,
  contratos binários e estados importam mais que testes que repetem o código.
- Este plano não solicita agentes paralelos nem aprovações adicionais para
  tarefas reversíveis; respeitar as permissões efetivas do ambiente.
