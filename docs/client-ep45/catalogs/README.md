# Catálogos e manifestos

`loose-files.json` identifica os arquivos soltos da instalação. Ele não
contém configurações, dumps ou executáveis: somente metadados e hashes.
Não representa a extração do SAF nem prova compatibilidade de formatos.

Após A0/A1, `loose-files.current.json` registra a configuração atual;
o manifesto anterior foi preservado. Só `CONFIG.INI` mudou. O índice interno
completo tem 23.570 registros e fica no cache devido ao tamanho (~20 MB),
com caminho/hash em `extraction-report.json`.

As saídas atuais incluem `baseline-evidence.json`, `extraction-report.json`,
`data-sources.json`, `map-files.json` e `asset-summary.json`. Esses catálogos
identificam fontes e recursos; não são tabelas de registros de gameplay.

Gerar novamente na raiz do projeto, usando apenas Python 3:

```bash
python3 tools/ep45-client/inventory.py --client-dir '/caminho/para/RebirthEvolution' --baseline-id rebirth-evolution-ep45-98c7dd3a --output docs/client-ep45/catalogs/loose-files.json
```

A ferramenta lê arquivos em blocos e recusa saída dentro do cliente.
Detecta alterações de tamanho/data durante o hash e registra symlinks
ignorados. A data de geração muda entre execuções; IDs, caminhos e hashes
devem permanecer iguais quando os arquivos da amostra não mudarem.

## Entregas previstas

| Arquivo | Conteúdo |
| --- | --- |
| `archive-files.jsonl` | Uma linha por entrada SAH, com ordinal, caminho original/normalizado, offset, tamanho, versão e hash do conteúdo |
| `extraction-report.json` | Contagens declaradas/lidas/extraídas, erros, duplicatas, distribuição de formatos e integridade |
| `items.jsonl` | Itens com chave original `(type,typeId)` e relações |
| `skills.jsonl` | Skills/níveis/buffs e seus vínculos |
| `mobs.jsonl` / `npcs.jsonl` | Entidades, recursos e dados presentes no cliente |
| `quests.jsonl` | Etapas, textos, requisitos e recompensas exibidas |
| `maps.jsonl` | Mapas e relações com recursos/regiões/portais/posicionamentos presentes |
| `assets.jsonl` | Modelos, texturas, animações, áudio, efeitos, interface e fontes |
| `strings.jsonl` | Textos, encoding, idioma, IDs e usos |

Criar catálogos adicionais conforme o inventário revelar novos sistemas.
Não criar arquivos vazios para aparentar que a extração foi concluída.

Cada linha normalizada deve referenciar o registro original, o manifesto,
o schema e uma evidência conforme `../schemas/provenance.schema.json`.
Manter números originais, unidades, valores ausentes e campos desconhecidos;
não preencher ausências com defaults de EP8. Separar dado bruto de derivado.

As exportações devem ter ordenação determinística e versão de schema.
JSONL grande pode ficar no cache, com contagem/hash/caminho e instrução de
geração versionados. Os relatórios devem identificar referências quebradas,
IDs duplicados, entidades sem recursos e recursos sem entidade.
