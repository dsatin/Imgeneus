#!/usr/bin/env bash
# Usage:
#   bash deploy/seed-levels.sh
#   bash deploy/seed-levels.sh --apply
#   bash deploy/seed-levels.sh --rollback deploy/backups/seed-levels-YYYYmmdd-HHMMSS
# Rollback preview is the default; add --apply to execute it.
# Requires a healthy MySQL 8.0 and migrated shaiya.levels (InnoDB).
# Stop world before applying; start it only after this command succeeds.
set -euo pipefail
umask 077
VERSION=1.0.0
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
COMPOSE=(docker compose -f compose.linux.yml)
APPLY=0
ROLLBACK=
COMMAND=$(printf '%q ' "$0" "$@")
while (($#)); do
    case "$1" in
        --apply) APPLY=1; shift ;;
        --rollback) ROLLBACK=${2:?Missing backup directory}; shift 2 ;;
        *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
    esac
done
MODE=DRY-RUN
if ((APPLY)); then MODE=APPLY; fi
for binary in docker jq awk sha256sum diff flock mktemp df date hostname tee cp mv sort wc sed; do
    command -v "$binary" >/dev/null || { printf 'Missing binary: %s\n' "$binary" >&2; exit 1; }
done
mkdir -p deploy/logs
test -w deploy/logs
exec 9>deploy/logs/seed-levels.lock
flock -n 9 || { echo 'Another seed operation is running.' >&2; exit 1; }
STAMP=$(date +%Y%m%d-%H%M%S)
LOG="deploy/logs/seed-levels-$STAMP-$$.log"
exec > >(tee -a "$LOG") 2>&1
WORK=$(mktemp -d)
SCANNED=0; TO_CHANGE=0; CHANGED=0; SKIPPED=0; FAILED=0
finish() {
    local status=$?
    trap - EXIT
    if ((status)); then FAILED=$((FAILED + 1)); fi
    printf 'Summary: scanned=%s / to_change=%s / changed=%s / skipped=%s / failed=%s\n' \
        "$SCANNED" "$TO_CHANGE" "$CHANGED" "$SKIPPED" "$FAILED"
    rm -rf -- "$WORK"
    exit "$status"
}
trap finish EXIT
trap 'printf "Error at line %s; aborting.\n" "$LINENO" >&2' ERR
sql() {
    "${COMPOSE[@]}" exec -T mysql sh -c \
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --skip-column-names shaiya' "$@"
}
snapshot() {
    printf 'SELECT Id, Level, Mode, Exp FROM levels ORDER BY Id;\n' | sql > "$1.tmp"
    mv "$1.tmp" "$1"
}
hash() { sha256sum "$1" | awk '{print $1}'; }
item_hash() { printf '%s' "$1" | sha256sum | awk '{print $1}'; }
emit_items() {
    local action=$1 before=$2 after=$3 id value old
    awk -F '\t' '{print $1}' "$before" "$after" | sort -nu > "$WORK/ids"
    SCANNED=$(wc -l < "$WORK/ids")
    while IFS= read -r id; do
        old=$(awk -F '\t' -v id="$id" '$1==id' "$before")
        value=$(awk -F '\t' -v id="$id" '$1==id' "$after")
        if [[ "$old" == "$value" ]]; then
            SKIPPED=$((SKIPPED + 1))
            printf '[%s] skip shaiya.levels/%s :: %s -> %s\n' "$MODE" "$id" "${old:-absent}" "${value:-absent}"
        else
            TO_CHANGE=$((TO_CHANGE + 1))
            printf '[%s] %s shaiya.levels/%s :: %s -> %s\n' "$MODE" "$action" "$id" "${old:-absent}" "${value:-absent}"
        fi
    done < "$WORK/ids"
}
backup() {
    local before=$1 after=$2 action=$3 id old value before_hash after_hash
    mkdir -p deploy/backups
    test -w deploy/backups
    local available required
    available=$(df -Pk deploy/backups | awk 'END {print $4 * 1024}')
    required=$(( $(wc -c < "$before") + $(wc -c < "$after") + 10485760 ))
    awk -v available="$available" -v required="$required" 'BEGIN {exit !(available > required)}'
    BACKUP="deploy/backups/seed-levels-$STAMP"
    if [[ -e "$BACKUP" ]]; then echo 'Backup path already exists; retry next second.' >&2; exit 1; fi
    mkdir -p "$BACKUP/data/shaiya"
    cp -a "$before" "$BACKUP/data/shaiya/levels.tsv.tmp"
    mv "$BACKUP/data/shaiya/levels.tsv.tmp" "$BACKUP/data/shaiya/levels.tsv"
    cp -a "$after" "$BACKUP/expected.tsv.tmp"
    mv "$BACKUP/expected.tsv.tmp" "$BACKUP/expected.tsv"
    # The counter changes on insertion; compare structural schema independently.
    printf 'SHOW CREATE TABLE levels;\n' | sql | sed 's/ AUTO_INCREMENT=[0-9]*//g' > "$BACKUP/schema.tsv.tmp"
    mv "$BACKUP/schema.tsv.tmp" "$BACKUP/schema.tsv"
    : > "$WORK/items.jsonl"
    while IFS= read -r id; do
        old=$(awk -F '\t' -v id="$id" '$1==id' "$before")
        value=$(awk -F '\t' -v id="$id" '$1==id' "$after")
        before_hash=$(item_hash "$old"); after_hash=$(item_hash "$value")
        jq -nc --arg target "shaiya.levels/$id" --arg before "$old" --arg after "$value" \
            --arg before_sha256 "$before_hash" --arg after_sha256 "$after_hash" \
            '{target:$target,before:$before,after:$after,before_sha256:$before_sha256,after_sha256:$after_sha256}' >> "$WORK/items.jsonl"
    done < "$WORK/ids"
    jq -n --arg timestamp "$(date -Is)" --arg host "$(hostname)" --arg version "$VERSION" \
        --arg command_line "$COMMAND" --arg action "$action" \
        --arg before_sha256 "$(hash "$before")" --arg after_sha256 "$(hash "$after")" \
        --arg schema_sha256 "$(hash "$BACKUP/schema.tsv")" --slurpfile items "$WORK/items.jsonl" \
        '{timestamp:$timestamp,host:$host,script_version:$version,command_line:$command_line,action:$action,
          before_sha256:$before_sha256,after_sha256:$after_sha256,schema_sha256:$schema_sha256,items:$items}' \
        > "$BACKUP/manifest.json.tmp"
    mv "$BACKUP/manifest.json.tmp" "$BACKUP/manifest.json"
    [[ "$(hash "$BACKUP/data/shaiya/levels.tsv")" == "$(hash "$before")" ]]
    [[ "$(hash "$BACKUP/expected.tsv")" == "$(hash "$after")" ]]
    printf 'Backup: %s\n' "$BACKUP"
}
# All database writes run in one transaction; mysql stops on the first error.
# A disconnected or failed session rolls back its uncommitted changes.
write_rows() {
    local rows=$1
    {
        printf 'START TRANSACTION;\nDELETE FROM levels;\n'
        awk -F '\t' 'NF==4 {printf "INSERT INTO levels (Id,Level,Mode,Exp) VALUES (%s,%s,%s,%s);\n",$1,$2,$3,$4}' "$rows"
        printf 'COMMIT;\n'
    } > "$WORK/write.sql.tmp"
    mv "$WORK/write.sql.tmp" "$WORK/write.sql"
    sql < "$WORK/write.sql"
    snapshot "$WORK/verified.tsv"
    diff -u "$rows" "$WORK/verified.tsv"
    CHANGED=$TO_CHANGE
}
"${COMPOSE[@]}" config --quiet
MYSQL_ID=$("${COMPOSE[@]}" ps -q mysql)
[[ -n "$MYSQL_ID" ]]
[[ "$(docker inspect -f '{{.State.Health.Status}}' "$MYSQL_ID")" == healthy ]]
printf 'SELECT VERSION();\n' | sql > "$WORK/version"
[[ "$(cat "$WORK/version")" == 8.0.* ]]
[[ "$(printf "SELECT ENGINE FROM information_schema.tables WHERE table_schema='shaiya' AND table_name='levels';\n" | sql)" == InnoDB ]]
if ((APPLY)) && [[ -n "$("${COMPOSE[@]}" ps --status running -q world)" ]]; then
    echo 'Stop world before applying seed or rollback.' >&2; exit 1
fi
snapshot "$WORK/before.tsv"
if [[ -n "$ROLLBACK" ]]; then
    MANIFEST="$ROLLBACK/manifest.json"
    [[ "$(jq -r .script_version "$MANIFEST")" == "$VERSION" ]]
    [[ "$(hash "$ROLLBACK/data/shaiya/levels.tsv")" == "$(jq -r .before_sha256 "$MANIFEST")" ]]
    [[ "$(hash "$ROLLBACK/expected.tsv")" == "$(jq -r .after_sha256 "$MANIFEST")" ]]
    printf 'SHOW CREATE TABLE levels;\n' | sql | sed 's/ AUTO_INCREMENT=[0-9]*//g' > "$WORK/schema.tsv"
    [[ "$(hash "$WORK/schema.tsv")" == "$(jq -r .schema_sha256 "$MANIFEST")" ]]
    cp -a "$ROLLBACK/data/shaiya/levels.tsv" "$WORK/after.tsv"
    if ! diff -q "$WORK/before.tsv" "$WORK/after.tsv" >/dev/null; then
        [[ "$(hash "$WORK/before.tsv")" == "$(jq -r .after_sha256 "$MANIFEST")" ]] || \
            { echo 'Table changed since backup; refusing to overwrite newer data.' >&2; exit 1; }
    fi
    emit_items restore "$WORK/before.tsv" "$WORK/after.tsv"
else
    awk '/^\([0-9]+,/ {gsub(/[(),;]/, ""); gsub(/ +/, "\t"); print}' \
        src/Imgeneus.Database/Migrations/sql/InitLevels.sql > "$WORK/after.tsv"
    [[ -s "$WORK/after.tsv" ]]
    if [[ -s "$WORK/before.tsv" ]] && ! diff -q "$WORK/before.tsv" "$WORK/after.tsv" >/dev/null; then
        echo 'Nonempty levels differs from repository seed; refusing to overwrite it.' >&2; exit 1
    fi
    emit_items seed "$WORK/before.tsv" "$WORK/after.tsv"
fi
if ((APPLY && TO_CHANGE)); then
    ACTION=seed
    if [[ -n "$ROLLBACK" ]]; then ACTION=rollback; fi
    backup "$WORK/before.tsv" "$WORK/after.tsv" "$ACTION"
    # Recheck the exact snapshot after all backups succeed and before writing.
    snapshot "$WORK/check.tsv"
    diff -u "$WORK/before.tsv" "$WORK/check.tsv"
    write_rows "$WORK/after.tsv"
fi
