# Inventário e extração do cliente

Ferramentas Python 3 sem dependências externas, SDK .NET ou Docker.
Executar na raiz do repositório. Os arquivos do cliente são somente fonte
de leitura; o cache e os relatórios ficam separados.

```bash
EP45_CLIENT_DIR='/home/dsatin/Games/Heroic/Prefixes/Shaiya EP 4.5/drive_c/RebirthEvolution'
EP45_CACHE='.client-ep45-cache/rebirth-evolution-ep45-98c7dd3a'

python3 tools/ep45-client/inventory.py --client-dir "$EP45_CLIENT_DIR" --baseline-id rebirth-evolution-ep45-98c7dd3a --output docs/client-ep45/catalogs/loose-files.current.json

python3 tools/ep45-client/baseline.py --client-dir "$EP45_CLIENT_DIR" --manifest docs/client-ep45/catalogs/loose-files.current.json --snapshot-dir "$EP45_CACHE/originals" --output docs/client-ep45/catalogs/baseline-evidence.json

python3 tools/ep45-client/archive.py extract --client-dir "$EP45_CACHE/originals" --output-dir "$EP45_CACHE" --report-dir docs/client-ep45/catalogs --baseline-id rebirth-evolution-ep45-98c7dd3a --expected-manifest docs/client-ep45/catalogs/loose-files.current.json

python3 tools/ep45-client/discover.py --manifest "$EP45_CACHE/archive-files.jsonl" --extraction-report docs/client-ep45/catalogs/extraction-report.json --output-dir docs/client-ep45/catalogs
```

`baseline.py` aceita `--original-game` para preservar/conferir uma cópia
pré-patch e `--heroic-config` com `--game-id` para registrar somente opções
permitidas do runner. As configurações completas e argumentos potencialmente
sensíveis não são publicados. Sem esses parâmetros, a identificação continua
funcionando; a evidência registra somente as informações disponíveis.

`archive.py inventory` lê o índice, valida e calcula hashes das faixas sem
extrair os conteúdos. O modo `extract` também compara cada arquivo de saída
com a sua faixa no SAF. Ambos verificam o hash completo SAH/SAF antes/depois.
Assinatura/contagens de índice cifrado não suportadas geram erro explícito.

## Cache e retomada

| Caminho no cache | Conteúdo |
| --- | --- |
| `originals/` | Amostra congelada e executável original quando disponível |
| `extracted/tree/` | Árvore principal com nomes/case preservados |
| `extracted/duplicates/<ordinal>/` | Entradas repetidas, sem substituir a primeira |
| `extracted/supplemental/<ordinal>/` | Registros após a árvore, separados da fonte ativa |
| `archive-files.jsonl` | Todas as entradas, origem, offsets, hashes, classificação e resultado |
| `archive-folders.json` | Árvore/contagens originais das pastas |
| `unreferenced-ranges.jsonl` | Intervalos do SAF que não pertencem às entradas catalogadas |

O cache não entra no Git nem no build Docker. O manifesto completo tem
aproximadamente 20 MB e fica no cache; seu caminho/hash e os resumos são
versionados em `docs/client-ep45/catalogs/`.

Reexecutar o mesmo comando `extract` para retomar: arquivos existentes são
lidos e conferidos, sem substituição. Conteúdo divergente gera erro e mantém
o arquivo existente. Interrupções deixam o manifesto `.pending`, sem
promovê-lo a resultado válido; saídas temporárias não são entradas concluídas.

As datas dos arquivos originais estão no manifesto externo. Os arquivos
extraídos têm as datas da extração; não há timestamp por entrada no layout
SAH identificado. Campos sem semântica comprovada permanecem desconhecidos.

## Testes

```bash
python3 tools/ep45-client/test_archive.py
```

Cobrem truncamento, contagens/ranges inválidos, UTF-8 inválido, duplicatas,
case, intervalos aninhados, paths externos, conflitos arquivo/pasta,
symlinks, conteúdo corrompido, retomada e incompatibilidade de baseline.

Essas ferramentas extraem arquivos e identificam containers. Ainda não
descriptografam SData nem decodificam registros de itens, skills ou mobs.
