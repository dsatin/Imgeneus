# Imgeneus on Linux

Test environment: Docker Compose, MySQL 8.0, Login/World services targeting
the EP8 ps0032 client linked in the main README. SDK 8 builds the .NET 6 target;
the runtime remains .NET 6. No global dotnet installation is required on Manjaro.

## Configuration

Local `.env` contains two random passwords and uses mode 0600. Keep it private.
`.env.example` documents variables. On a new checkout, copy it to `.env`, set
random passwords, and run `chmod 600 .env`. Data persists in
`imgeneus-local_mysql-data`; MySQL exposes no host port. HTTP panels bind locally.

Original commits for three submodules were unavailable remotely. This checkout uses:

| Submodule | Commit |
| --- | --- |
| Imgeneus.Authentication | `77b3a65e9a0ba60f83e1aa452e9f0b997ea27a70` |
| LiteNetwork | `3dad300d984abae0c2aee53f0054683353023181` |
| Sylver.HandlerInvoker | `6b8edfb704ea5a28eb9663ed6c39c08d8f62e2b0` |
| Parsec | `ebac92c473175a5c0aae29c1e370a2a299d1dedc` |

The Dockerfile applies `deploy/litenetwork-compat.patch` inside the image,
restoring the expected user collection, silent disconnection, and connection
callbacks without changing the submodule checkout.

It also applies `sylver-interface-compat.patch` and `sylver-invoker-compat.patch`.
Public Sylver lacks `InvokeAsync` and the `IServiceScope` signature used by
Login/World. These patches restore the signature, use the connection scope,
and await asynchronous handlers before disposing their resources.

Builds run `CompatibilityChecks` for synchronous/asynchronous invocation,
packet transformation, optional parameters, session isolation, and exception
propagation, without additional test packages.

Diagnose the running Login without creating accounts or changing records:

```bash
docker build --target build --build-arg SERVER=Login -f deploy/Linux.Dockerfile -t imgeneus-local-checks .
docker run --rm --network imgeneus-local_default imgeneus-local-checks dotnet /source/deploy/CompatibilityChecks/bin/Release/net8.0/CompatibilityChecks.dll --login login 30800
```

This check completes RSA handshake, sends AES-encrypted authentication for
a nonexistent account, and validates the encrypted response.

## Operations

Run from the repository root with access to the Docker daemon:

```bash
docker compose -f compose.linux.yml build login world
docker compose -f compose.linux.yml up -d
docker compose -f compose.linux.yml ps
docker compose -f compose.linux.yml logs --tail=100 login world
```

Before Login starts, `shaiya-users` must exist and `imgeneus` needs permissions.
MySQL creates `shaiya` automatically; applications run their own migrations.
This machine's accounts database and grants were prepared during deployment.
For a new volume, start `mysql` first, then use the following commands:

```bash
docker compose -f compose.linux.yml exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -e "CREATE DATABASE IF NOT EXISTS \`shaiya-users\`;"'
docker compose -f compose.linux.yml exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -e "GRANT ALL PRIVILEGES ON \`shaiya-users\`.* TO '\''imgeneus'\''@'\''%'\'';"'
```

Do not reuse a volume with a different `lower_case_table_names` value: this
setting is fixed at volume creation.

Populate 320 level records after migrations:

```bash
docker compose -f compose.linux.yml stop world
bash deploy/seed-levels.sh
bash deploy/seed-levels.sh --apply
docker compose -f compose.linux.yml up -d world
```

The script refuses to replace differing nonempty data, writes logs under
`deploy/logs`, backs up before writing, and inserts in one transaction.
Rerunning with identical data does not create another backup.

Rollback with World stopped:

```bash
bash deploy/seed-levels.sh --rollback deploy/backups/seed-levels-YYYYmmdd-HHMMSS
bash deploy/seed-levels.sh --rollback deploy/backups/seed-levels-YYYYmmdd-HHMMSS --apply
docker compose -f compose.linux.yml up -d world
```

Rollback also backs up current state and refuses changed data since the
original operation. Existing seeds are infrastructure, not EP4.5 client evidence.

## Client

Register at `http://127.0.0.1:7000/Identity/Account/Register`. Existing code gives
the first account the superadministrator role.

The [upstream setup guide](https://github.com/aosyatnik/Imgeneus/blob/master/INSTALL.md)
describes ps0032 IP/credential launch arguments. From the executable directory:

```bash
wine game.exe start 127.0.0.1 'YOUR_USERNAME:YOUR_PASSWORD'
```

On Windows: `game.exe start 127.0.0.1 YOUR_USERNAME:YOUR_PASSWORD`. The address
is Login TCP 30800. Login announces World, here `127.0.0.1` TCP 30810; a separate
World argument is unnecessary. Heroic/GE-Proton on Manjaro validated login,
selection, character creation, and world entry. In Heroic, select `game.exe`
and set `start 127.0.0.1 YOUR_USERNAME:YOUR_PASSWORD` as arguments.

Default configuration targets EP8 ps0032. Parsec episode enums concern data
reading, not backend protocol compatibility.

### Experimental EP4.5 test

The Rebirth Evolution test client completed handshake, login, selection,
creation, first map entry, and logout. Its `CHARACTER_ITEMS` (`0x0106`) reader
uses 34-byte records: bag/slot/type/typeId, two-byte quality, six one-byte gems,
count, and 21-byte craft name. Larger EP8 records caused a fault at
`game.exe+0x17ce8d`.

The experimental profile is configured with:

```dotenv
WORLD_LEGACY_INVENTORY=true
WORLD_LOG_LEVEL=Trace
```

Once changes are ready to validate, build/recreate World:

```bash
docker compose -f compose.linux.yml build world
docker compose -f compose.linux.yml up -d --no-deps world
```

Diagnostics record packet codes/sizes without contents. This option affects
all World sessions; use `false` for EP8. Full EP4.5 compatibility is not established:
item movement, combat, and other formats need validation. The additional
character-list writer uses eight equipment types/IDs, a 19-byte name, and
deletion/rename flags based on reader `0x57C790`; it is not compiled or tested.
Second entry after logout failed in the earlier observed session.

This English variant has an embedded Login IP; EP8 arguments did not replace
it. The installation uses `127.0.0.1` TCP 30800 and `start game` in Heroic.
Login announces World TCP 30810. Original executable SHA-256:
`45755d927ee66c7c5e354defb5e8f9329f8f21848307e62797f368dee2c33f91`.
English Login address file offset: `0x2A9B84`. Other binaries may differ.
See [client baseline](../docs/client-ep45/baseline.md) for full provenance.

## External access

The current protocol announces IPv4. For a public IPv6 connection, use a VPN
providing participants with IPv4. After configuring the VPN, set `.env`:

```dotenv
GAME_BIND_IP=<local VPN IPv4>
WORLD_ADVERTISED_IPV4=<same VPN IPv4>
```

Recreate Login/World with `docker compose -f compose.linux.yml up -d`.
Local/external clients use that IPv4 and TCP 30800/30810. VPN/firewall setup
is not automated.

## Stop

```bash
docker compose -f compose.linux.yml stop
```

This preserves data. `down -v` removes volumes.
