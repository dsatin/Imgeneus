# Estrutura SAH/SAF confirmada nesta amostra

Fonte: baseline `rebirth-evolution-ep45-98c7dd3a`, hashes do
[relatório](../catalogs/extraction-report.json). Leitor de infraestrutura
comparado: Parsec `ebac92c473175a5c0aae29c1e370a2a299d1dedc`, classes
`Sah`, `SFolder`, `SFile` e `SBinaryReader`. A confirmação nesta amostra vem
das contagens, limites e comparação dos bytes/hashes efetivamente extraídos.

## Cabeçalho e árvore

| Offset | Tamanho | Campo observado |
| --- | --- | --- |
| 0 | 3 | Assinatura ASCII `SAH` |
| 3 | 4 | Versão signed int32 little-endian, valor 0 |
| 7 | 4 | Contagem declarada signed int32, 23.564 |
| 11 | 40 | Bytes de preenchimento, preservados no relatório |
| 51 | Variável | Pasta raiz e árvore recursiva |

Cada pasta contém nome com comprimento int32 little-endian, contagem de
arquivos, registros de arquivos, contagem de subpastas e subpastas recursivas.
O comprimento do nome conta bytes, incluindo o terminador zero presente.
Os nomes desta amostra passaram na leitura UTF-8 estrita.

Cada registro de arquivo contém nome com comprimento, offset int64 no SAF,
tamanho int32 e versão int32. Os nomes/campos originais e os offsets do SAH
ficam no manifesto. O tamanho é usado em **bytes**, confirmado pela leitura
exata e hashes; o comentário "kbs" de `SFile.Length` não foi usado como unidade.
A finalidade do campo de versão não foi determinada.

O início do SAF desta amostra não possui assinatura `SAF`; o leitor usa
intervalos do índice. Não inserir ou remover cabeçalhos para compensar isso.

## Pós-árvore e intervalos desconhecidos

A árvore terminou em 911.317 de 911.512 bytes do SAH. Os 195 bytes restantes
se ajustam exatamente a: count int32 = 6, seis registros com formato de
arquivo e int32 final = 0. Não há nome de pasta nesse bloco.

Os nomes são dois `Cash.Sdata`, `Skill.SData`, `Item.SData` e dois `rest space`.
Foram extraídos separadamente e receberam IDs `supplemental-*`. A semântica
do bloco e seu uso pelo cliente permanecem desconhecidos; não substituir
as tabelas ativas por esses conteúdos.

Há 95.141.488 bytes do SAF fora da união das entradas principais e
suplementares. Seus intervalos estão no cache e seu manifesto/hash no
[resumo de recursos](../catalogs/asset-summary.json). Isso não prova que
sejam dados inúteis ou arquivos recuperáveis. O SAF completo foi congelado
para análise posterior, preservando também esses bytes.

## Duplicata

`Item/3DO/10051__.3do` aparece nos ordinais 14.672 e 14.912, em offsets
diferentes. Os dois conteúdos têm 13.204 bytes e SHA-256 idêntico:
`728a400f349ff114a0d0a66f022e41b5fef98e6339f200869a26d5930c880da8`.
Ambos foram preservados. A precedência de lookup no cliente ainda não foi
analisada; o comportamento de um dicionário do Parsec não é prova dela.
