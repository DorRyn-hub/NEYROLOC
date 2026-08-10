# Серверная часть NEYROLOC (мульти-тенант)

```
телефон ──HTTPS──▶ VPS ──▶ frps ──туннель──▶ ПК пользователя :8765
                    │
                    ├── Caddy   — TLS: обычный для сайта, on-demand для поддоменов
                    ├── broker  — выдаёт поддомены, авторизует туннели (:9001, localhost)
                    └── frps    — приём туннелей (:7000), vhost :8080
```

## Файлы
- `broker.py` — сервис-брокер (только stdlib):
  - `POST /api/register` — десктоп получает личный поддомен + секрет + параметры frps;
  - `GET /api/check` — Caddy спрашивает, выпускать ли сертификат (on-demand TLS);
  - `POST /handler` — плагин frps: `Login` проверяет секрет, `NewProxy` не даёт занять чужой поддомен, неизвестные операции отклоняются;
  - JSON-тело ограничено 64 КиБ (переопределяется через `NEYROLOC_MAX_REQUEST_BODY_BYTES`);
  - `X-Forwarded-For` учитывается только для соединений от loopback proxy (Caddy).
- `landing.html` — публичная страница продукта.
- `deploy_phase2.sh` — установка: broker (systemd) + Caddyfile + frps.toml + лендинг.

## Развёртывание
Залить на VPS `broker.py`, `landing.html`, `mark.svg`, `rdev.svg`, `NEYROLOC.apk` в `/tmp/`, затем:

```bash
bash deploy_phase2.sh
```

## DNS
- `neyroloc.<домен>` A → IP VPS — сайт и API;
- `*.neyroloc.<домен>` A → IP VPS — поддомены пользователей (обязательно **DNS only**, без прокси Cloudflare: иначе ломается frp и выпуск сертификатов).

## Состояние
Реестр арендаторов: `/var/lib/neyroloc/registry.json` (0600, в нём секреты).
Токен frps: `/etc/frp/token`.

Broker должен оставаться привязанным к `127.0.0.1`: наружу публикуются только
маршруты, явно проксируемые Caddy. После обновления сначала проверьте
`python3 -m unittest discover -s tests -v`; deploy-скрипт меняет systemd/Caddy/frps
и должен запускаться только вручную на целевом VPS.
