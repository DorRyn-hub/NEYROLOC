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
import ipaddress
import os
import re
import secrets
import string
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DOMAIN = os.environ.get("NEYROLOC_BASE_DOMAIN", "neyroloc.static-assets-io.website")
REGISTRY_PATH = Path(os.environ.get("NEYROLOC_REGISTRY", "/var/lib/neyroloc/registry.json"))
LISTEN_PORT = int(os.environ.get("NEYROLOC_BROKER_PORT", "9001"))
MAX_REQUEST_BODY_BYTES = int(os.environ.get("NEYROLOC_MAX_REQUEST_BODY_BYTES", "65536"))
MAX_PATH_LENGTH = 2_048
MAX_CONCURRENT_REQUESTS = 64

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
MAX_RATE_LIMIT_CLIENTS = 10_000
REGISTRY_TOUCH_INTERVAL_SECONDS = 60

_ALPHABET = string.ascii_lowercase + string.digits
_SUBDOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$")


class RequestBodyError(ValueError):
    """A malformed HTTP request body that should be returned as JSON."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class Registry:
    """Реестр арендаторов в JSON-файле под мьютексом."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        self._data = self._read()

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {"users": {}}
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"registry is unreadable: {self.path}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("users", {}), dict):
            raise RuntimeError(f"registry has an invalid shape: {self.path}")
        data.setdefault("users", {})
        for subdomain, entry in data["users"].items():
            if (
                not isinstance(subdomain, str)
                or not _SUBDOMAIN_RE.fullmatch(subdomain)
                or not isinstance(entry, dict)
                or not isinstance(entry.get("secret"), str)
                or not entry["secret"]
            ):
                raise RuntimeError(f"registry contains an invalid tenant: {self.path}")
        return data

    def _write(self) -> None:
        payload = json.dumps(self._data, ensure_ascii=False, indent=2) + "\n"
        fd, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        try:
            try:
                os.fchmod(fd, 0o600)
            except OSError:
                pass
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                fd = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            try:
                self.path.chmod(0o600)  # в файле секреты арендаторов
            except OSError:
                pass
            directory_fd = None
            try:
                directory_fd = os.open(self.path.parent, os.O_RDONLY)
                os.fsync(directory_fd)
            except OSError:
                pass
            finally:
                if directory_fd is not None:
                    os.close(directory_fd)
        except BaseException:
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                temporary.unlink()
            except OSError:
                pass
            raise

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
        with self._lock:
            entry = self._data.get("users", {}).get(sub)
            return dict(entry) if isinstance(entry, dict) else None

    def touch(self, sub: str) -> None:
        with self._lock:
            entry = self._data.get("users", {}).get(sub)
            if entry is not None:
                now = int(time.time())
                if now - int(entry.get("last_seen") or 0) < REGISTRY_TOUCH_INTERVAL_SECONDS:
                    return
                entry["last_seen"] = now
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
        if len(_register_hits) >= MAX_RATE_LIMIT_CLIENTS:
            stale = [
                key
                for key, values in _register_hits.items()
                if not values or now - values[-1] >= 3600
            ]
            for key in stale:
                _register_hits.pop(key, None)
        if ip not in _register_hits and len(_register_hits) >= MAX_RATE_LIMIT_CLIENTS:
            return False
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
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _path_allowed(self) -> bool:
        if len(self.path) <= MAX_PATH_LENGTH:
            return True
        self._json({"error": "request path too long"}, 414)
        return False

    def _body(self) -> dict:
        raw_length = self.headers.get("Content-Length") or "0"
        try:
            length = int(raw_length)
        except (TypeError, ValueError) as exc:
            raise RequestBodyError(400, "invalid Content-Length") from exc
        if length < 0:
            raise RequestBodyError(400, "invalid Content-Length")
        if length > MAX_REQUEST_BODY_BYTES:
            raise RequestBodyError(413, "request body too large")
        if not length:
            return {}
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise RequestBodyError(400, "incomplete request body")
            data = json.loads(raw)
        except RequestBodyError:
            raise
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise RequestBodyError(400, "invalid JSON body") from exc
        if not isinstance(data, dict):
            raise RequestBodyError(400, "JSON body must be an object")
        return data

    def _client_ip(self) -> str:
        peer = str(self.client_address[0])
        try:
            peer_ip = ipaddress.ip_address(peer)
        except ValueError:
            return peer

        # Broker слушает loopback; доверяем X-Forwarded-For только от локального
        # reverse proxy. Прямой удалённый клиент не может подменить rate-limit IP.
        if not peer_ip.is_loopback:
            return peer
        fwd = self.headers.get("X-Forwarded-For", "")
        candidate = fwd.split(",")[0].strip() if fwd else ""
        if not candidate:
            return peer
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return peer

    def _read_json_or_reply(self) -> dict | None:
        try:
            return self._body()
        except RequestBodyError as exc:
            # BaseHTTPRequestHandler uses HTTP/1.0 here, but explicitly closing
            # also makes the oversized-body behavior safe if the protocol changes.
            self.close_connection = True
            self._json({"error": exc.message}, exc.status)
            return None

    # ----- маршруты -----

    def do_GET(self) -> None:  # noqa: N802 — stdlib API
        if not self._path_allowed():
            return
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
        if not self._path_allowed():
            return
        parsed = urlparse(self.path)

        if parsed.path == "/api/register":
            data = self._read_json_or_reply()
            if data is None:
                return
            if not _rate_ok(self._client_ip()):
                self._json({"error": "too many registrations, try later"}, 429)
                return
            frps_token = _frps_token()
            if not frps_token or not 1 <= FRPS_PORT <= 65_535:
                self._json({"error": "tunnel service is not configured"}, 503)
                return
            raw_name = data.get("name")
            name = raw_name if isinstance(raw_name, str) else "device"
            name = "".join(char for char in name if char >= " " and char != "\x7f")
            entry = registry.create(name.strip() or "device")
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
                "frps_token": frps_token,
            })
            return

        # Плагин frps: Login и NewProxy.
        if parsed.path == "/handler":
            data = self._read_json_or_reply()
            if data is not None:
                self._handle_frps(data)
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

        # Новые/неожиданные операции не должны обходить tenant-авторизацию.
        reject("unsupported operation")


class BoundedThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = MAX_CONCURRENT_REQUESTS

    def __init__(self, *args, max_workers: int = MAX_CONCURRENT_REQUESTS, **kwargs) -> None:
        self._request_slots = threading.BoundedSemaphore(max_workers)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address) -> None:
        if not self._request_slots.acquire(blocking=False):
            body = b'{"error":"server busy"}'
            try:
                request.sendall(
                    b"HTTP/1.0 503 Service Unavailable\r\n"
                    b"Content-Type: application/json\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode("ascii")
                    + b"Connection: close\r\n\r\n"
                    + body
                )
            except OSError:
                pass
            self.close_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._request_slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


def main() -> None:
    if not 1 <= LISTEN_PORT <= 65_535:
        raise SystemExit("invalid NEYROLOC_BROKER_PORT")
    server = BoundedThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Handler)
    print(f"neyroloc-broker on 127.0.0.1:{LISTEN_PORT}, domain={BASE_DOMAIN}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
