#!/usr/bin/env python3
"""NEYROLOC broker — выдача поддоменов и авторизация туннелей.

Одна служба закрывает три задачи мульти-тенанта:

1. /api/register — десктоп при первом включении публичного доступа получает
   свой поддомен и секрет (никаких общих токенов на всех).
2. /api/check    — Caddy спрашивает, можно ли выпускать сертификат для хоста
   (on-demand TLS): отвечаем 200 только для зарегистрированных поддоменов.
3. /handler      — frps спрашивает при подключении клиента (server plugin):
   проверяем секрет и то, что клиент занимает СВОЙ поддомен, а не чужой.

Только stdlib: на VPS ничего доустанавливать не нужно.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import string
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DOMAIN = os.environ.get("NEYROLOC_BASE_DOMAIN", "neyroloc.static-assets-io.website")
REGISTRY_PATH = Path(os.environ.get("NEYROLOC_REGISTRY", "/var/lib/neyroloc/registry.json"))
LISTEN_PORT = int(os.environ.get("NEYROLOC_BROKER_PORT", "9001"))

# Что отдаём клиенту, чтобы ему не пришлось ничего зашивать в приложение.
FRPS_HOST = os.environ.get("NEYROLOC_FRPS_HOST", BASE_DOMAIN)
FRPS_PORT = int(os.environ.get("NEYROLOC_FRPS_PORT", "7000"))
FRPS_TOKEN_FILE = Path(os.environ.get("NEYROLOC_FRPS_TOKEN_FILE", "/etc/frp/token"))


def _frps_token() -> str:
    try:
        return FRPS_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""

# Сколько регистраций разрешаем с одного IP в час — грубая защита от перебора.
REGISTER_LIMIT_PER_HOUR = 20

_ALPHABET = string.ascii_lowercase + string.digits
_SUBDOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$")


class Registry:
    """Реестр арендаторов в JSON-файле под мьютексом."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._read()

    def _read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"users": {}}

    def _write(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        try:
            self.path.chmod(0o600)          # в файле секреты арендаторов
        except OSError:
            pass

    def create(self, name: str) -> dict:
        with self._lock:
            users = self._data.setdefault("users", {})
            for _ in range(50):
                sub = "".join(secrets.choice(_ALPHABET) for _ in range(10))
                if sub not in users:
                    break
            else:
                raise RuntimeError("не удалось подобрать свободный поддомен")
            entry = {
                "secret": secrets.token_hex(24),
                "name": name[:60],
                "created": int(time.time()),
                "last_seen": 0,
            }
            users[sub] = entry
            self._write()
            return {"subdomain": sub, **entry}

    def get(self, sub: str) -> dict | None:
        return self._data.get("users", {}).get(sub)

    def touch(self, sub: str) -> None:
        with self._lock:
            entry = self._data.get("users", {}).get(sub)
            if entry is not None:
                entry["last_seen"] = int(time.time())
                self._write()

    def known_host(self, host: str) -> bool:
        host = host.lower().strip()
        if host == BASE_DOMAIN:
            return True
        suffix = "." + BASE_DOMAIN
        if not host.endswith(suffix):
            return False
        return self.get(host[: -len(suffix)]) is not None


registry = Registry(REGISTRY_PATH)
_register_hits: dict[str, list[float]] = {}
_hits_lock = threading.Lock()


def _rate_ok(ip: str) -> bool:
    now = time.time()
    with _hits_lock:
        hits = [t for t in _register_hits.get(ip, []) if now - t < 3600]
        if len(hits) >= REGISTER_LIMIT_PER_HOUR:
            _register_hits[ip] = hits
            return False
        hits.append(now)
        _register_hits[ip] = hits
        return True


class Handler(BaseHTTPRequestHandler):
    server_version = "neyroloc-broker"

    def log_message(self, *args) -> None:      # не спамим в journal
        pass

    # ----- helpers -----

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _client_ip(self) -> str:
        # За Caddy реальный адрес приходит в X-Forwarded-For.
        fwd = self.headers.get("X-Forwarded-For", "")
        return fwd.split(",")[0].strip() if fwd else self.client_address[0]

    # ----- маршруты -----

    def do_GET(self) -> None:  # noqa: N802 — stdlib API
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._json({"ok": True, "domain": BASE_DOMAIN})
            return

        # Caddy on-demand TLS: выпускать ли сертификат для этого хоста?
        if parsed.path == "/api/check":
            host = (parse_qs(parsed.query).get("domain") or [""])[0]
            if registry.known_host(host):
                self._json({"ok": True})
            else:
                self._json({"error": "unknown host"}, 404)
            return

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 — stdlib API
        parsed = urlparse(self.path)

        if parsed.path == "/api/register":
            if not _rate_ok(self._client_ip()):
                self._json({"error": "too many registrations, try later"}, 429)
                return
            data = self._body()
            entry = registry.create(str(data.get("name", "") or "device"))
            sub = entry["subdomain"]
            self._json({
                "subdomain": sub,
                "secret": entry["secret"],
                "domain": BASE_DOMAIN,
                "url": f"https://{sub}.{BASE_DOMAIN}",
                # Параметры подключения к frps: клиент их только применяет.
                # Общий токен не является границей безопасности — доступ
                # разграничивают secret арендатора и проверка в /handler.
                "server": FRPS_HOST,
                "port": FRPS_PORT,
                "frps_token": _frps_token(),
            })
            return

        # Плагин frps: Login и NewProxy.
        if parsed.path == "/handler":
            self._handle_frps(self._body())
            return

        self.send_error(404)

    # ----- логика авторизации frps -----

    def _handle_frps(self, payload: dict) -> None:
        op = payload.get("op")
        content = payload.get("content") or {}

        def reject(reason: str) -> None:
            self._json({"reject": True, "reject_reason": reason})

        if op == "Login":
            user = str(content.get("user") or "")
            metas = content.get("metas") or {}
            entry = registry.get(user)
            if entry is None:
                reject("unknown client")
                return
            # secrets.compare_digest — чтобы сравнение не зависело от времени.
            if not secrets.compare_digest(str(metas.get("secret") or ""), entry["secret"]):
                reject("bad secret")
                return
            registry.touch(user)
            self._json({"unchange": True})
            return

        if op == "NewProxy":
            user = str((content.get("user") or {}).get("user") or "")
            subdomain = str(content.get("subdomain") or "")
            if registry.get(user) is None:
                reject("unknown client")
                return
            # Ключевое правило мульти-тенанта: занять можно только свой поддомен.
            if subdomain != user:
                reject("subdomain does not belong to this client")
                return
            self._json({"unchange": True})
            return

        # Незнакомая операция — не мешаем.
        self._json({"unchange": True})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Handler)
    print(f"neyroloc-broker on 127.0.0.1:{LISTEN_PORT}, domain={BASE_DOMAIN}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
