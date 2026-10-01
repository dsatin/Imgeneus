# Baseline do snapshot

## Projeto

Fork existente: <https://github.com/dsatin/Imgeneus>.
Branch de trabalho: `develop/ep45-compatibility`.
Base Linux: `63e0248ab148481dabe8394a34edd06720525b09`.
`master` preservada: `0ce355594d521c3a06a08f24d0a9b60ebc8a459f`.

| Submódulo | Commit usado |
| --- | --- |
| Imgeneus.Authentication | `77b3a65e9a0ba60f83e1aa452e9f0b997ea27a70` |
| LiteNetwork | `3dad300d984abae0c2aee53f0054683353023181` |
| Sylver.HandlerInvoker | `6b8edfb704ea5a28eb9663ed6c39c08d8f62e2b0` |
| Parsec | `ebac92c473175a5c0aae29c1e370a2a299d1dedc` |

As adaptações de infraestrutura Linux estão descritas em
[deploy/README.md](../../deploy/README.md). O Docker aplica os patches dos
submódulos na build. O SDK não está instalado globalmente nesta máquina;
as ferramentas de extração ainda precisam ter sua execução definida.

## Cliente

Instalação informada pelo usuário como EP 4.5, Rebirth Evolution, em:

```text
/home/dsatin/Games/Heroic/Prefixes/Shaiya EP 4.5/drive_c/RebirthEvolution
```

| Arquivo/variante | SHA-256 |
| --- | --- |
| `game.exe` original, registrado antes do patch | `45755d927ee66c7c5e354defb5e8f9329f8f21848307e62797f368dee2c33f91` |
| `game.exe` com IP local, reconferido em 2026-10-01 | `98c7dd3a0589d5695e489d81b1acffdd456c633b47e913757b67e5f492d5ec48` |
| `data.sah`, reconferido em 2026-10-01 | `6ad31356e94e243b45d4f4a6ffe881d76dd945a0e4f7f22687ebdf6026bf7f3c` |
| `data.saf`, inventário externo em 2026-10-01 | `e3c7f3a8268d5242b6199b99ca482c3390fc012fad2257dd155b1e35794d5e7b` |

O executável é PE32/x86. Tamanhos observados: `game.exe` 3.219.456 bytes,
`data.sah` 911.512 bytes, `data.saf` 2.487.238.964 bytes.
O manifesto externo registra hashes e tamanhos dos arquivos soltos;
os arquivos internos do SAF ainda não foram inventariados.

`Version.ini` declara `CheckVersion=3`, `CurrentVersion=5`,
`StartUpdate=UPDATE_END`. Esses valores não são prova de episódio.

O patch local alterou somente o endereço inglês embutido no offset de
arquivo `0x2A9B84`: slot de 16 bytes com `92.55.147.107`, substituído por
`127.0.0.1` com preenchimento zero. O cliente inglês não utilizou o IP dos
argumentos no teste. Argumentos atuais: `start game`. Outras builds podem
ter endereços e offsets diferentes.

Ambiente usado nas sessões: Manjaro, Heroic e GE-Proton. Login TCP 30800 e
World TCP 30810 locais. Completar em A0 as versões exatas e parâmetros que
forem necessários à reprodução; não publicar credenciais ou arquivos de
configuração contendo contas.

## O que foi observado e o que está pendente

| Item | Estado e evidência |
| --- | --- |
| Login e criação de personagem | Confirmados pelo usuário no cliente com IP local |
| Crash na primeira entrada | Wine registrou falha em `0x0057CE8D`; leitor `0x57CC60` usava registro menor que o enviado pelo EP8 |
| Inventário inicial | Writer de 34 bytes e limites de bags/slots; checks da build anterior passaram |
| Envio após desconexão | Guarda contra socket/sender descartado; check da build anterior passou |
| Primeiro acesso ao mapa | Confirmado pelo usuário; logs registraram `CHARACTER_ENTERED_MAP` |
| Logout | Confirmado pelo usuário; logs registraram remoção e envio de `LOGOUT` |
| Segunda entrada na mesma sessão | Falhou; não houve novo `SELECT_CHARACTER` nos logs observados |
| Seleção de personagens EP4.5 | Writer adicional preparado após inspeção de `0x57C790`; ainda não compilado/testado |
| Demais funcionalidades | Não validadas integralmente com este cliente |

O snapshot contém código experimental além da imagem World em execução.
As compilações da última alteração de seleção foram interrompidas antes
de iniciar; não existe resultado válido dessa build. Nenhum reinício de
serviço é necessário para criar esta documentação e publicar o snapshot.

O nome histórico da opção é `WorldServer:LegacyInventoryPackets`, configurada
por `WORLD_LEGACY_INVENTORY`; agora ela também seleciona o writer experimental
da lista de personagens no código. Seu padrão permanece `false`. A etapa B
deverá substituir esse experimento por um perfil de protocolo bem definido.
