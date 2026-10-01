# Protocolo: evidências iniciais

Esta referência é parcial. O catálogo completo C→S/S→C ainda precisa ser
derivado do executável. Os nomes abaixo seguem o código existente por
conveniência; o layout EP8 não deve ser presumido compatível.

| Opcode | Uso observado/analisado | Estado |
| --- | --- | --- |
| `0xA301` | Handshake World | Recebido nas sessões locais; especificação completa pendente |
| `0x0101` | Lista de personagens S→C | Leitor em `0x57C790`; writer novo ainda não validado |
| `0x0104` | Seleção de personagem | Primeira seleção/entrada observadas; repetição pendente |
| `0x0105` | Detalhes do personagem S→C | Enviado na primeira entrada; todos os campos ainda precisam de auditoria |
| `0x0106` | Inventário inicial S→C | Registro de 34 bytes identificado; primeira entrada confirmada |
| `0x0107` | Logout | Fluxo recebido/respondido; retorno completo à seleção pendente |
| `0x0109` | Facção/limite de modo S→C | Observado; efeito sobre estado da UI exige documentação |
| `0x010B` | Barra de atalhos | Leitor do cliente indica count + registros de 5 bytes; comparar ambas as direções |
| `0x0201` | Entrada no mapa C→S | Recebido após carregamento na sessão local |
| `0xB106` | Pacote relacionado ao início do mundo | Recebido; nome histórico `CHANGE_ENCRYPTION`, sem semântica completa confirmada |

## Inventário inicial `0x0106`

Leitor do cliente em `0x57CC60`. Payload começa com count de 1 byte;
cada registro tem 34 bytes:

| Offset no registro | Tamanho | Campo |
| --- | --- | --- |
| 0 | 1 | Bag |
| 1 | 1 | Slot |
| 2 | 1 | Type |
| 3 | 1 | TypeId |
| 4 | 2 | Quality, little-endian |
| 6 | 6 | Seis identificadores de gemas de 1 byte |
| 12 | 1 | Count |
| 13 | 21 | Craft name, campo fixo com terminador |

O leitor aloca seis bags × 24 slots. A falha observada ocorreu em
`0x57CE8D` ao interpretar os registros maiores do EP8. O writer experimental
rejeita bags/slots fora desse intervalo e gemas não representáveis em 1 byte.
Os demais pacotes de inventário ainda precisam de mapeamento.

## Seleção de personagens `0x0101`

O leitor em `0x57C790` consome slot, ID e, para ID não zero, dados básicos,
oito tipos e oito IDs de equipamentos, seguidos de 21 bytes. A interpretação
implementada no writer é nome de 19 bytes e dois indicadores históricos de
exclusão/renomeação; confirmar a semântica desses indicadores nos fluxos da
UI. Há seis bytes adicionais quando o tipo do equipamento de índice 7 não
é zero. Não enviar os arrays de 17 elementos/campos extras do serializer EP8.

O writer adicional foi preparado, mas ainda não foi compilado nem exercitado.
A ausência de segunda seleção nos logs após logout não confirma por si só
que o formato desse pacote é a causa do problema.

## Criptografia e estados

O código atual usa AES na seleção e chave expandida XOR nas respostas do
mundo. O envio da barra de atalhos está ligado à mudança de modo no cliente;
o dispatch de logout chama `0x4015A0`. Documentar integralmente derivação,
contadores, buffers, ordem e efeitos de transição antes de modificar a sessão.
Ainda não existe especificação completa desses estados para a amostra.

Cada novo pacote deve ter ID de especificação, direção, layout com offsets,
variantes/limites, rotina C→S/S→C e evidências estáticas/de execução. Bytes
cifrados e respostas do nosso servidor não bastam para inferir campos.
