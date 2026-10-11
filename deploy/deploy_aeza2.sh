#!/usr/bin/env bash
# Безопасное совместное развёртывание NEYROLOC на AEZA-2.
# Xray Reality на 443 и сервисы RDev9 не изменяются и не перезапускаются.
set -Eeuo pipefail

BASE_DOMAIN="neyroloc.static-assets-io.website"
PUBLIC_HTTPS_PORT=7443
STAGE_DIR="${NEYROLOC_STAGE_DIR:-/root/neyroloc-stage}"
BACKUP_ROOT="${NEYROLOC_BACKUP_ROOT:-/root/neyroloc-backups}"
CADDY_IMPORT="import /etc/caddy/neyroloc.caddy"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Нужен root." >&2
    exit 1
fi

for tool in /usr/bin/caddy /usr/local/bin/frps python3 curl ss systemctl; do
    if ! command -v "$tool" >/dev/null 2>&1 && [[ ! -x "$tool" ]]; then
        echo "Не найден обязательный инструмент: $tool" >&2
        exit 1
    fi
done

required=(
    broker.py Caddyfile.aeza2 frps.aeza2.toml.template
    neyroloc-broker.service caddy-reliability.conf registry.json token landing.html
    mark.svg rdev.svg Onest-Regular.ttf Onest-Bold.ttf NEYROLOC-Android.apk
)
for name in "${required[@]}"; do
    if [[ ! -s "$STAGE_DIR/$name" ]]; then
        echo "Не найден или пуст: $STAGE_DIR/$name" >&2
        exit 1
    fi
done

if ss -ltnp "sport = :$PUBLIC_HTTPS_PORT" | tail -n +2 | grep -qv caddy; then
    echo "Порт $PUBLIC_HTTPS_PORT занят не Caddy; развёртывание остановлено." >&2
    exit 1
fi
if ss -ltnp "sport = :7000" | tail -n +2 | grep -qv frps; then
    echo "Порт 7000 занят не frps; развёртывание остановлено." >&2
    exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="$BACKUP_ROOT/$timestamp"
work="$(mktemp -d /root/neyroloc-deploy.XXXXXX)"
umask 077
install -d -m 0700 "$backup"

cleanup() {
    rm -rf "$work"
}
trap cleanup EXIT

backup_file() {
    local source="$1" label="$2"
    if [[ -e "$source" ]]; then
        cp -a "$source" "$backup/$label"
    else
        : > "$backup/$label.absent"
    fi
}

restore_file() {
    local label="$1" destination="$2"
    if [[ -e "$backup/$label.absent" ]]; then
        rm -f "$destination"
    else
        cp -a "$backup/$label" "$destination"
    fi
}

backup_file /etc/caddy/Caddyfile Caddyfile
backup_file /etc/caddy/neyroloc.caddy neyroloc.caddy
backup_file /etc/systemd/system/caddy.service.d/neyroloc-reliability.conf caddy-reliability.conf
backup_file /etc/frp/frps.toml frps.toml
backup_file /etc/frp/token token
backup_file /etc/systemd/system/frps.service frps.service
backup_file /etc/systemd/system/neyroloc-broker.service neyroloc-broker.service
backup_file /opt/neyroloc/broker.py broker.py
backup_file /var/lib/neyroloc/registry.json registry.json

caddy_was_active="$(systemctl is-active caddy 2>/dev/null || true)"
frps_was_active="$(systemctl is-active frps 2>/dev/null || true)"
frps_was_enabled="$(systemctl is-enabled frps 2>/dev/null || true)"
broker_was_active="$(systemctl is-active neyroloc-broker 2>/dev/null || true)"
broker_was_enabled="$(systemctl is-enabled neyroloc-broker 2>/dev/null || true)"
xray_pid_before="$(systemctl show xray -p MainPID --value)"

rollback() {
    local rc=$?
    trap - ERR
    set +e
    systemctl disable --now neyroloc-broker frps >/dev/null 2>&1
    restore_file Caddyfile /etc/caddy/Caddyfile
    restore_file neyroloc.caddy /etc/caddy/neyroloc.caddy
    restore_file caddy-reliability.conf /etc/systemd/system/caddy.service.d/neyroloc-reliability.conf
    restore_file frps.toml /etc/frp/frps.toml
    restore_file token /etc/frp/token
    restore_file frps.service /etc/systemd/system/frps.service
    restore_file neyroloc-broker.service /etc/systemd/system/neyroloc-broker.service
    restore_file broker.py /opt/neyroloc/broker.py
    restore_file registry.json /var/lib/neyroloc/registry.json
    systemctl daemon-reload
    [[ "$frps_was_enabled" == enabled ]] && systemctl enable frps >/dev/null 2>&1
    [[ "$broker_was_enabled" == enabled ]] && systemctl enable neyroloc-broker >/dev/null 2>&1
    [[ "$frps_was_active" == active ]] && systemctl restart frps >/dev/null 2>&1
    [[ "$broker_was_active" == active ]] && systemctl restart neyroloc-broker >/dev/null 2>&1
    [[ "$caddy_was_active" == active ]] && systemctl reload caddy >/dev/null 2>&1
    echo "Развёртывание откатилось. Backup: $backup" >&2
    exit "$rc"
}
trap rollback ERR

# Секрет не попадает в argv или stdout: Python читает оба файла напрямую.
python3 - "$STAGE_DIR/frps.aeza2.toml.template" "$STAGE_DIR/token" "$work/frps.toml" <<'PY'
import re
import sys
from pathlib import Path

template_path, token_path, output_path = map(Path, sys.argv[1:])
token = token_path.read_text(encoding="utf-8").strip()
if not re.fullmatch(r"[A-Za-z0-9._-]{16,256}", token):
    raise SystemExit("invalid FRPS token")
template = template_path.read_text(encoding="utf-8")
if template.count("__FRPS_TOKEN__") != 1:
    raise SystemExit("invalid FRPS template")
output_path.write_text(template.replace("__FRPS_TOKEN__", token), encoding="utf-8")
output_path.chmod(0o600)
PY

awk -v import_line="$CADDY_IMPORT" '$0 != import_line' \
    /etc/caddy/Caddyfile > "$work/Caddyfile.base"
first_directive="$(awk '!/^[[:space:]]*(#|$)/ { print; exit }' "$work/Caddyfile.base")"
if [[ "$first_directive" == "{" ]]; then
    echo "В Caddyfile уже есть глобальный блок; нужен ручной merge." >&2
    exit 1
fi
{
    printf 'import %s\n\n' "$STAGE_DIR/Caddyfile.aeza2"
    awk -v import_line="$CADDY_IMPORT" '$0 != import_line' /etc/caddy/Caddyfile
} > "$work/Caddyfile.validate"
{
    printf '%s\n\n' "$CADDY_IMPORT"
    awk -v import_line="$CADDY_IMPORT" '$0 != import_line' /etc/caddy/Caddyfile
} > "$work/Caddyfile.final"

python3 -m py_compile "$STAGE_DIR/broker.py"
/usr/local/bin/frps verify -c "$work/frps.toml" >/dev/null
/usr/bin/caddy validate --config "$work/Caddyfile.validate" --adapter caddyfile >/dev/null

getent passwd neyroloc >/dev/null \
    || useradd --system --no-create-home --shell /usr/sbin/nologin neyroloc
install -d -o root -g root -m 0755 \
    /opt/neyroloc /etc/frp /var/www/neyroloc /var/www/neyroloc/fonts \
    /var/www/neyroloc/download
install -d -o root -g root -m 0755 /etc/systemd/system/caddy.service.d
install -d -o neyroloc -g neyroloc -m 0700 /var/lib/neyroloc
install -o root -g root -m 0755 "$STAGE_DIR/broker.py" /opt/neyroloc/broker.py
install -o neyroloc -g neyroloc -m 0600 \
    "$STAGE_DIR/registry.json" /var/lib/neyroloc/registry.json
install -o root -g neyroloc -m 0640 "$STAGE_DIR/token" /etc/frp/token
install -o root -g root -m 0600 "$work/frps.toml" /etc/frp/frps.toml
install -o root -g root -m 0644 \
    "$STAGE_DIR/neyroloc-broker.service" /etc/systemd/system/neyroloc-broker.service
install -o root -g root -m 0644 "$STAGE_DIR/Caddyfile.aeza2" /etc/caddy/neyroloc.caddy
install -o root -g root -m 0644 \
    "$STAGE_DIR/caddy-reliability.conf" \
    /etc/systemd/system/caddy.service.d/neyroloc-reliability.conf
install -o root -g root -m 0644 "$STAGE_DIR/landing.html" /var/www/neyroloc/index.html
install -o root -g root -m 0644 "$STAGE_DIR/mark.svg" /var/www/neyroloc/mark.svg
install -o root -g root -m 0644 "$STAGE_DIR/rdev.svg" /var/www/neyroloc/rdev.svg
install -o root -g root -m 0644 \
    "$STAGE_DIR/Onest-Regular.ttf" /var/www/neyroloc/fonts/Onest-Regular.ttf
install -o root -g root -m 0644 \
    "$STAGE_DIR/Onest-Bold.ttf" /var/www/neyroloc/fonts/Onest-Bold.ttf
install -o root -g root -m 0644 \
    "$STAGE_DIR/NEYROLOC-Android.apk" /var/www/neyroloc/download/NEYROLOC-Android.apk
install -o root -g root -m 0644 \
    "$STAGE_DIR/NEYROLOC-Android.apk" /var/www/neyroloc/download/android
for package in NEYROLOC-Linux.AppImage NEYROLOC-macOS.dmg NEYROLOC-Windows.zip; do
    if [[ -s "$STAGE_DIR/$package" ]]; then
        install -o root -g root -m 0644 \
            "$STAGE_DIR/$package" "/var/www/neyroloc/download/$package"
    fi
done

install -o root -g root -m 0644 "$work/Caddyfile.final" /etc/caddy/Caddyfile
/usr/bin/caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null
systemctl daemon-reload
systemctl enable neyroloc-broker
systemctl restart neyroloc-broker
ready=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS --max-time 2 http://127.0.0.1:9001/api/health >/dev/null; then
        ready=1
        break
    fi
    sleep 1
done
[[ "$ready" -eq 1 ]]
systemctl enable --now frps
systemctl is-active --quiet frps
systemctl reload caddy
systemctl is-active --quiet caddy
systemctl is-active --quiet xray
[[ "$xray_pid_before" == "$(systemctl show xray -p MainPID --value)" ]]

trap - ERR
echo "AEZA2_DEPLOY_OK"
echo "Backup: $backup"
