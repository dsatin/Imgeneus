# Análise do executável

Os endereços conhecidos são da amostra identificada em `../baseline.md`.
Não reutilizar offsets cegamente em outro executável.

| Endereço virtual/offset | Observação |
| --- | --- |
| VA `0x5867F0` | Dispatch de vários pacotes recebidos do World |
| VA `0x57C790` | Leitor de lista de personagens |
| VA `0x57CC60` | Leitor de inventário inicial |
| VA `0x57CE8D` | Instrução da falha de inventário observada |
| VA `0x580A00` | Leitor da barra de atalhos; chamado para `0x010B` |
| VA `0x401570` / `0x4015A0` | Funções relacionadas ao modo de descriptografia na entrada/logout |
| Offset de arquivo `0x2A9B84` | Endereço de Login inglês alterado localmente |

Antes de converter endereços, ler a tabela de seções PE; RVA, endereço
virtual e offset de arquivo são grandezas distintas. Anotar arquitetura,
base, hash do binário e versão da ferramenta em cada relatório.

Exemplo de inspeção limitada, sem modificar o cliente:

```bash
EP45_CLIENT_DIR='/caminho/para/RebirthEvolution'
objdump -h "$EP45_CLIENT_DIR/game.exe"
objdump -d -Mintel --start-address=0x57c790 --stop-address=0x57ca50 "$EP45_CLIENT_DIR/game.exe"
```

Guardar disassembly completo no cache, publicar somente trechos necessários
e mapas de função/evidência. A análise dinâmica deve explicar o cenário e
correlacionar a função com ações da UI. Strings e nomes herdados do backend
são pistas, não confirmação de semântica.
