# NEYROLOC — удалённый доступ (Фаза 1)

Публичный адрес: **https://neyroloc.static-assets-io.website**

Схема: телефон → Caddy(TLS) на VPS → frps → **frpc на этом Mac** → localhost:8765 (десктоп NEYROLOC).

## Как поднять туннель вручную (пока не встроено в приложение)
1. Запусти десктоп NEYROLOC → «Файл → Удалённый доступ с телефона» (сервер на :8765).
2. Запусти клиент туннеля:
   ```bash
   ./remote/frpc-darwin-arm64 -c ./remote/frpc.toml
   ```
3. На телефоне в приложении адрес: `https://neyroloc.static-assets-io.website`, далее код сопряжения.

## VPS (130.12.46.155)
- frps: /etc/frp/frps.toml (systemd `frps`), токен в /etc/frp/token
- Caddy: /etc/caddy/Caddyfile (systemd `caddy`), авто-Let's Encrypt
- доступ по SSH-ключу (пароль отключить/сменить)

frpc.toml и бинарник в .gitignore (в конфиге — токен frps).
