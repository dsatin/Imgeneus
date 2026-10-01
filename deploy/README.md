# Imgeneus no Linux

Ambiente de teste: Docker Compose, MySQL 8.0 e serviços Login/World para o
cliente EP8 ps0032 indicado no README principal. O SDK 8 compila o alvo
.NET 6; o runtime continua sendo .NET 6. Não é necessário instalar dotnet
no Manjaro.

## Configuração

O arquivo `.env` local contém duas senhas aleatórias e tem permissão 0600.
Não publique esse arquivo. `.env.example` documenta as variáveis. Em um
novo checkout, copie `.env.example` para `.env`, substitua as duas senhas
por valores aleatórios e restrinja suas permissões com `chmod 600 .env`.
Os dados ficam no volume `imgeneus-local_mysql-data`; MySQL não publica
porta no host. Os painéis HTTP ficam restritos a localhost.

Os commits originais de três submódulos não estavam disponíveis no remoto.
O checkout de teste usa:

| Submódulo | Commit |
| --- | --- |
| Imgeneus.Authentication | `77b3a65e9a0ba60f83e1aa452e9f0b997ea27a70` |
| LiteNetwork | `3dad300d984abae0c2aee53f0054683353023181` |
| Sylver.HandlerInvoker | `6b8edfb704ea5a28eb9663ed6c39c08d8f62e2b0` |
| Parsec | `ebac92c473175a5c0aae29c1e370a2a299d1dedc` |

O Dockerfile aplica `deploy/litenetwork-compat.patch` somente na imagem:
restaura a coleção de usuários, a desconexão silenciosa e os eventos de
conexão/desconexão esperados pelo Imgeneus. O checkout do submódulo não
é alterado pelo patch.

Também aplica `sylver-interface-compat.patch` e `sylver-invoker-compat.patch`
na imagem. A versão pública do Sylver não implementa `InvokeAsync` nem a
assinatura com `IServiceScope` usada pelos clientes Login/World. Os patches
restauram essa assinatura, usam o escopo da conexão e aguardam os handlers
assíncronos antes de liberar seus recursos.

Cada build executa `CompatibilityChecks`: verifica chamadas síncronas e
assíncronas, transformação dos pacotes, parâmetros opcionais, isolamento
das sessões e propagação de exceções. Não adiciona pacotes de teste.

Para diagnosticar o Login em execução, sem criar conta ou atualizar registros:

```bash
docker build --target build --build-arg SERVER=Login -f deploy/Linux.Dockerfile -t imgeneus-local-checks .
docker run --rm --network imgeneus-local_default imgeneus-local-checks dotnet /source/deploy/CompatibilityChecks/bin/Release/net8.0/CompatibilityChecks.dll --login login 30800
```

Esse teste completa o handshake RSA, envia autenticação criptografada por AES
para uma conta inexistente e valida a resposta criptografada do servidor.

## Operação

Execute na raiz do projeto, com acesso ao daemon Docker:

```bash
docker compose -f compose.linux.yml build login world
docker compose -f compose.linux.yml up -d
docker compose -f compose.linux.yml ps
docker compose -f compose.linux.yml logs --tail=100 login world
```

O banco `shaiya-users` precisa existir e o usuário `imgeneus` precisa ter
permissões nele antes da primeira inicialização do Login. O MySQL cria
`shaiya` automaticamente; cada aplicação executa suas próprias migrações.
Nesta máquina, o banco de contas e as permissões foram preparados durante
a implantação. Em um volume novo, após iniciar apenas `mysql`, execute:

```bash
docker compose -f compose.linux.yml exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -e "CREATE DATABASE IF NOT EXISTS \`shaiya-users\`;"'
docker compose -f compose.linux.yml exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -e "GRANT ALL PRIVILEGES ON \`shaiya-users\`.* TO '\''imgeneus'\''@'\''%'\'';"'
```

Não reutilize o volume com outra configuração de
`lower_case_table_names`: esse parâmetro é definido na criação do volume.

Para preencher os 320 registros de níveis após as migrações:

```bash
docker compose -f compose.linux.yml stop world
bash deploy/seed-levels.sh
bash deploy/seed-levels.sh --apply
docker compose -f compose.linux.yml up -d world
```

O script recusa sobrescrever uma tabela não vazia diferente da fonte,
grava logs em `deploy/logs`, faz backup antes de escrever e insere os dados
numa única transação. Reexecutar com os mesmos dados não cria novo backup.

Rollback, com World parado:

```bash
bash deploy/seed-levels.sh --rollback deploy/backups/seed-levels-YYYYmmdd-HHMMSS
bash deploy/seed-levels.sh --rollback deploy/backups/seed-levels-YYYYmmdd-HHMMSS --apply
docker compose -f compose.linux.yml up -d world
```

O rollback também faz backup do estado atual e recusa alterar a tabela se
ela tiver mudado desde a operação original.

## Cliente

Crie a conta em `http://127.0.0.1:7000/Identity/Account/Register`.
A primeira conta recebe o papel de superadministrador pelo código existente.

O [guia do projeto de origem](https://github.com/aosyatnik/Imgeneus/blob/master/INSTALL.md)
documenta a inicialização do cliente ps0032 com IP e credenciais como argumentos.
No terminal, dentro da pasta que contém `game.exe`, use no Manjaro:

```bash
wine game.exe start 127.0.0.1 'YOUR_USERNAME:YOUR_PASSWORD'
```

No Windows, use `game.exe start 127.0.0.1 YOUR_USERNAME:YOUR_PASSWORD`.
O IP informado é o do Login, TCP 30800. Após selecionar o servidor, o Login
anuncia o endereço do World: nesta implantação, `127.0.0.1`, TCP 30810.
Não é necessário informar o IP do World no comando. O cliente foi validado
no Manjaro usando Heroic com GE-Proton: login, seleção de personagens,
criação de personagem e entrada no mundo. No Heroic, configure `game.exe`
como executável e `start 127.0.0.1 YOUR_USERNAME:YOUR_PASSWORD` como argumentos.

A configuração padrão implementa EP8 ps0032. As enumerações de episódios
no Parsec se referem à leitura de arquivos de dados, não à compatibilidade
dos clientes com o servidor.

### Teste experimental com EP4.5

O cliente Rebirth Evolution de 2011 completou handshake, login, seleção e
criação de personagem. Seu leitor do pacote `CHARACTER_ITEMS` (`0x0106`)
usa registros de 34 bytes: bag/slot/type/typeId, quality de 2 bytes, seis
gemas de 1 byte, count e craft name de 21 bytes. O formato EP8 inclui gemas
de 4 bytes e campos adicionais e causou uma falha em `game.exe+0x17ce8d`.

Para testar a adaptação das listas de inventário e de personagens, configure:

```dotenv
WORLD_LEGACY_INVENTORY=true
WORLD_LOG_LEVEL=Trace
```

Compile e recrie apenas World:

```bash
docker compose -f compose.linux.yml build world
docker compose -f compose.linux.yml up -d --no-deps world
```

O diagnóstico registra códigos e tamanhos dos pacotes, sem seu conteúdo.
A opção vale para todo o World; use `false` para o cliente EP8. Esta alteração
não representa suporte completo ao EP4.5: movimentação de itens, combate e
demais formatos ainda precisam de validação. A entrada no mapa e o logout foram
confirmados no cliente. O retorno à seleção usa oito tipos/IDs de equipamento,
nome de 19 bytes e indicadores de exclusão/renomeação, conforme o leitor em
`game.exe` no endereço `0x57C790`; a segunda entrada ainda requer teste manual.

Nessa variante inglesa, o IP de Login é embutido no executável; os argumentos
do EP8 não o substituem. A instalação local usa `127.0.0.1`, TCP 30800, e
`start game` no Heroic. O Login anuncia o World, TCP 30810. O executável original
tem SHA-256 `45755d927ee66c7c5e354defb5e8f9329f8f21848307e62797f368dee2c33f91`;
seu endereço inglês está no offset `0x2A9B84`. Outros executáveis podem ter
endereços e offsets diferentes.

## Acesso externo

O protocolo atual anuncia IPv4. Para acesso por uma conexão pública IPv6,
use uma VPN que forneça IPv4 aos participantes. Quando a VPN estiver
configurada, defina no `.env`:

```dotenv
GAME_BIND_IP=<IPv4 local da VPN>
WORLD_ADVERTISED_IPV4=<mesmo IPv4 da VPN>
```

Recrie Login e World com `docker compose -f compose.linux.yml up -d`.
Os clientes locais e externos devem usar esse IPv4. As portas necessárias
são TCP 30800 e 30810. A VPN e o firewall não são configurados automaticamente.

## Parar

```bash
docker compose -f compose.linux.yml stop
```

O comando preserva os dados. Evite `down -v`: ele remove os volumes.
