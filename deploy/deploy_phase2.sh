#!/usr/bin/env bash
# Фаза 2 на VPS: брокер поддоменов + on-demand TLS + мульти-тенант frps + лендинг.
set -euo pipefail

BASE_DOMAIN="neyroloc.static-assets-io.website"

echo ">>> каталоги"
install -d /opt/neyroloc /var/lib/neyroloc /var/www/neyroloc

echo ">>> брокер"
install -m 0755 /tmp/broker.py /opt/neyroloc/broker.py
cat > /etc/systemd/system/neyroloc-broker.service <<EOF
[Unit]
Description=NEYROLOC broker (subdomain provisioning + tunnel auth)
After=network.target

[Service]
Environment=NEYROLOC_BASE_DOMAIN=${BASE_DOMAIN}
Environment=NEYROLOC_REGISTRY=/var/lib/neyroloc/registry.json
ExecStart=/usr/bin/python3 /opt/neyroloc/broker.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now neyroloc-broker
sleep 1
systemctl is-active neyroloc-broker >/dev/null && echo "    broker: RUNNING"

echo ">>> лендинг + бренд-ассеты"
install -m 0644 /tmp/landing.html /var/www/neyroloc/index.html
install -m 0644 /tmp/mark.svg /var/www/neyroloc/mark.svg
install -m 0644 /tmp/rdev.svg /var/www/neyroloc/rdev.svg
install -d /var/www/neyroloc/download
[ -f /tmp/NEYROLOC.apk ] && install -m 0644 /tmp/NEYROLOC.apk /var/www/neyroloc/download/android

echo ">>> frps: мульти-тенант (поддомены + плагин авторизации)"
TOKEN=$(cat /etc/frp/token)
cat > /etc/frp/frps.toml <<EOF
bindPort = 7000
vhostHTTPPort = 8080
subDomainHost = "${BASE_DOMAIN}"

auth.method = "token"
auth.token = "${TOKEN}"

# Кто именно подключается и на какой поддомен имеет право — решает брокер.
[[httpPlugins]]
name = "neyroloc-broker"
addr = "127.0.0.1:9001"
path = "/handler"
ops = ["Login", "NewProxy"]
EOF
systemctl restart frps
sleep 1
systemctl is-active frps >/dev/null && echo "    frps: RUNNING"

echo ">>> Caddy: лендинг + API + on-demand TLS для поддоменов арендаторов"
cat > /etc/caddy/Caddyfile <<EOF
{
	# Сертификат для <клиент>.${BASE_DOMAIN} выпускается на лету, но только
	# если брокер подтвердит, что такой поддомен зарегистрирован.
	on_demand_tls {
		ask http://127.0.0.1:9001/api/check
	}
}

# Сайт продукта: лендинг + выдача поддоменов.
${BASE_DOMAIN} {
	handle /api/* {
		reverse_proxy 127.0.0.1:9001
	}
	handle {
		root * /var/www/neyroloc
		try_files {path} {path}/ /index.html
		file_server
	}
}

# Всё остальное — туннели пользователей.
https:// {
	tls {
		on_demand
	}
	reverse_proxy 127.0.0.1:8080
}
EOF
/usr/local/bin/caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null
systemctl restart caddy
sleep 4
systemctl is-active caddy >/dev/null && echo "    caddy: RUNNING"

echo "PHASE2_DONE"
