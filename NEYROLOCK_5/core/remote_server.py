"""Удалённый доступ с телефона через встроенный ограниченный HTTP-сервер.

Сервер остаётся dependency-free, не доверяет входным данным и использует код
сопряжения только один раз: после успешной проверки PWA получает временную
HttpOnly-сессию. Размер тела, истории и ответа ограничен.
"""

from __future__ import annotations

import hmac
import ipaddress
import json
import math
import secrets
import shutil
import socket
import sys
import threading
import time
from collections import deque
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Signal

from backends.base import Backend, Message

DEFAULT_PORT = 8765
MAX_REQUEST_BODY_BYTES = 1 * 1024 * 1024
MAX_HISTORY_MESSAGES = 128
MAX_MESSAGE_CHARS = 32_768
MAX_TOTAL_MESSAGE_CHARS = 262_144
MAX_SYSTEM_PROMPT_CHARS = 32_768
MAX_STREAM_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_PATH_LENGTH = 2_048
MAX_CONCURRENT_REQUESTS = 32
REQUEST_TIMEOUT_SECONDS = 30
SESSION_TTL_SECONDS = 12 * 60 * 60
MAX_SESSIONS = 64

AUTH_FAILURE_LIMIT = 8
AUTH_FAILURE_WINDOW_SECONDS = 60
API_REQUEST_LIMIT = 120
API_REQUEST_WINDOW_SECONDS = 60
CHAT_REQUEST_LIMIT = 12
CHAT_REQUEST_WINDOW_SECONDS = 60



def _first_existing(*paths: Path) -> Path:
    """Resolve a bundled data file while keeping source checkouts supported."""
    for path in paths:
        if path.is_file():
            return path
    return paths[0]


_MODULE_APP_ROOT = Path(__file__).resolve().parent.parent
_EXECUTABLE_ROOT = Path(sys.executable).resolve().parent
_BUNDLE_RESOURCES = _EXECUTABLE_ROOT.parent / "Resources"
_MOBILE_HTML = _first_existing(
    _MODULE_APP_ROOT / "resources" / "mobile.html",
    _EXECUTABLE_ROOT / "resources" / "mobile.html",
    _BUNDLE_RESOURCES / "resources" / "mobile.html",
)
_ANDROID_APK = _first_existing(
    _MODULE_APP_ROOT.parent / "packaging" / "android" / "NEYROLOC.apk",
    _EXECUTABLE_ROOT / "packaging" / "android" / "NEYROLOC.apk",
    _BUNDLE_RESOURCES / "packaging" / "android" / "NEYROLOC.apk",
)
_SESSION_COOKIE = "neyroloc_session"
_PRIVATE_V4_NETWORKS = tuple(
    ipaddress.ip_network(network) for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


class RequestError(ValueError):
    """A client request can be rejected before an application route runs."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class RateLimiter:
    """Small thread-safe sliding-window limiter keyed by untrusted clients."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit = limit
        self.window_seconds = float(window_seconds)
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if not events:
            # Keep the new deque while this call works with it; a later reset or
            # cleanup removes it. This avoids returning a detached container.
            self._events[key] = events
        return events

    def allow(self, key: str, *, now: float | None = None) -> tuple[bool, int]:
        current = time.monotonic() if now is None else now
        with self._lock:
            events = self._prune(key, current)
            if len(events) >= self.limit:
                retry = max(1, math.ceil(events[0] + self.window_seconds - current))
                return False, retry
            events.append(current)

            # Bound stale-key memory without trusting proxy-provided headers.
            if len(self._events) > 1_024:
                cutoff = current - self.window_seconds
                for old_key, old_events in list(self._events.items()):
                    if old_key != key and (not old_events or old_events[-1] <= cutoff):
                        self._events.pop(old_key, None)
            return True, 0

    def retry_after(self, key: str, *, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        with self._lock:
            events = self._prune(key, current)
            if len(events) < self.limit:
                return 0
            return max(1, math.ceil(events[0] + self.window_seconds - current))

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)


def _looks_lan(ip: str) -> bool:
    """Return whether *ip* is a valid RFC1918 IPv4 address."""
    try:
        address = ipaddress.ip_address(ip)
    except (TypeError, ValueError):
        return False
    return isinstance(address, ipaddress.IPv4Address) and any(
        address in network for network in _PRIVATE_V4_NETWORKS
    )


def local_ip() -> str:
    """IP этого компьютера в локальной Wi-Fi-сети."""
    import subprocess

    for iface in ("en0", "en1", "en2"):
        try:
            out = subprocess.run(
                ["ipconfig", "getifaddr", iface],
                capture_output=True,
                text=True,
                timeout=3,
            ).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out and _looks_lan(out):
            return out

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            candidate = sock.getsockname()[0]
            return candidate if _looks_lan(candidate) else "127.0.0.1"
    except OSError:
        return "127.0.0.1"


def tailscale_ip() -> str | None:
    """Tailscale-адрес этого Mac, если клиент установлен и запущен."""
    import subprocess

    candidates = [
        "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
        "/usr/local/bin/tailscale",
        "/opt/homebrew/bin/tailscale",
        "tailscale",
    ]
    for bin_path in candidates:
        try:
            out = subprocess.run(
                [bin_path, "ip", "-4"],
                capture_output=True,
                text=True,
                timeout=4,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out.returncode == 0:
            value = out.stdout.strip()
            ip = value.splitlines()[0].strip() if value else ""
            try:
                address = ipaddress.ip_address(ip)
            except ValueError:
                continue
            if isinstance(address, ipaddress.IPv4Address) and address in ipaddress.ip_network(
                "100.64.0.0/10"
            ):
                return ip
    return None


class RemoteBridge(QObject):
    """Потокобезопасный мост между HTTP-потоками и Qt-приложением."""

    statusChanged = Signal(str)
    modelChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.generation_lock = threading.Lock()
        self.phone_stop = threading.Event()
        self._state_lock = threading.RLock()
        self._backend: Backend | None = None
        self._backend_name = ""
        self._available_models: list[str] = []
        self._system_prompt = ""
        self._temperature = 0.7
        self._pair_code = ""
        self._sessions: dict[str, float] = {}
        self._shutting_down = threading.Event()
        self._active_remote_backend: Backend | None = None

    @property
    def backend(self) -> Backend | None:
        with self._state_lock:
            return self._backend

    @backend.setter
    def backend(self, value: Backend | None) -> None:
        with self._state_lock:
            previous = self._backend
            self._backend = value
        if previous is not None and previous is not value:
            # A stale phone request must stop before UI tears the old backend down.
            previous.cancel()

    @property
    def backend_name(self) -> str:
        with self._state_lock:
            return self._backend_name

    @backend_name.setter
    def backend_name(self, value: str) -> None:
        with self._state_lock:
            self._backend_name = str(value)

    @property
    def available_models(self) -> list[str]:
        with self._state_lock:
            return list(self._available_models)

    @available_models.setter
    def available_models(self, value: list[str]) -> None:
        with self._state_lock:
            self._available_models = [str(item) for item in value if str(item)]

    @property
    def system_prompt(self) -> str:
        with self._state_lock:
            return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        with self._state_lock:
            self._system_prompt = str(value)

    @property
    def temperature(self) -> float:
        with self._state_lock:
            return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = 0.7
        if not math.isfinite(parsed):
            parsed = 0.7
        with self._state_lock:
            self._temperature = min(max(parsed, 0.0), 2.0)

    @property
    def pair_code(self) -> str:
        with self._state_lock:
            return self._pair_code

    @pair_code.setter
    def pair_code(self, value: str) -> None:
        value = str(value)
        with self._state_lock:
            if value != self._pair_code:
                self._sessions.clear()
            self._pair_code = value

    def snapshot(self) -> dict[str, Any]:
        with self._state_lock:
            return {
                "backend": self._backend,
                "backend_name": self._backend_name,
                "models": list(self._available_models),
                "system": self._system_prompt,
                "temperature": self._temperature,
            }

    def verify_pair_code(self, candidate: str) -> bool:
        with self._state_lock:
            expected = self._pair_code
        if not expected or not candidate:
            return False
        return hmac.compare_digest(expected.encode("utf-8"), candidate.encode("utf-8"))

    def create_session(self) -> tuple[str, int]:
        token = secrets.token_urlsafe(32)
        expires_at = time.monotonic() + SESSION_TTL_SECONDS
        with self._state_lock:
            self._prune_sessions_locked()
            while len(self._sessions) >= MAX_SESSIONS:
                oldest = min(self._sessions, key=self._sessions.__getitem__)
                self._sessions.pop(oldest, None)
            self._sessions[token] = expires_at
        return token, SESSION_TTL_SECONDS

    def _prune_sessions_locked(self) -> None:
        now = time.monotonic()
        for token, expires_at in list(self._sessions.items()):
            if expires_at <= now:
                self._sessions.pop(token, None)

    def validate_session(self, token: str) -> bool:
        if not token or len(token) > 256:
            return False
        with self._state_lock:
            self._prune_sessions_locked()
            return token in self._sessions

    def authenticate(self, *, session: str = "") -> bool:
        """Authenticate API calls only with a short-lived paired session."""
        return self.validate_session(session)

    def revoke_sessions(self) -> None:
        with self._state_lock:
            self._sessions.clear()

    @property
    def shutting_down(self) -> bool:
        return self._shutting_down.is_set()

    def begin_remote_operation(self, backend: Backend) -> bool:
        with self._state_lock:
            if self._shutting_down.is_set() or backend is not self._backend:
                return False
            self._active_remote_backend = backend
            return True

    def end_remote_operation(self, backend: Backend) -> None:
        with self._state_lock:
            if self._active_remote_backend is backend:
                self._active_remote_backend = None

    @property
    def has_active_remote_operation(self) -> bool:
        with self._state_lock:
            return self._active_remote_backend is not None

    def cancel_remote_operation(self) -> None:
        self.phone_stop.set()
        with self._state_lock:
            backend = self._active_remote_backend
        if backend is not None:
            backend.cancel()

    def begin_shutdown(self) -> None:
        self._shutting_down.set()
        self.revoke_sessions()
        self.cancel_remote_operation()

    def end_shutdown(self) -> None:
        self.phone_stop.clear()
        self._shutting_down.clear()


class _Handler(BaseHTTPRequestHandler):
    bridge: RemoteBridge = None  # type: ignore[assignment]
    auth_limiter = RateLimiter(AUTH_FAILURE_LIMIT, AUTH_FAILURE_WINDOW_SECONDS)
    api_limiter = RateLimiter(API_REQUEST_LIMIT, API_REQUEST_WINDOW_SECONDS)
    chat_limiter = RateLimiter(CHAT_REQUEST_LIMIT, CHAT_REQUEST_WINDOW_SECONDS)
    server_version = "NEYROLOC"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(REQUEST_TIMEOUT_SECONDS)

    def log_message(self, *args) -> None:  # noqa: D401
        pass

    def _common_headers(self, cache_control: str = "no-store") -> None:
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")

    def _json(
        self,
        payload: dict[str, Any],
        status: int = 200,
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._common_headers()
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            pass

    def _read_body(self) -> dict[str, Any]:
        get_all = getattr(self.headers, "get_all", None)
        values = get_all("Content-Length") if callable(get_all) else None
        if values and len({value.strip() for value in values}) != 1:
            raise RequestError(400, "Противоречивый Content-Length.")
        raw_length = values[-1] if values else self.headers.get("Content-Length")
        if raw_length is None:
            return {}
        try:
            length = int(raw_length)
        except (TypeError, ValueError) as exc:
            raise RequestError(400, "Некорректный Content-Length.") from exc
        if length < 0:
            raise RequestError(400, "Некорректный Content-Length.")
        if length > MAX_REQUEST_BODY_BYTES:
            raise RequestError(413, "Запрос слишком большой.")
        if length == 0:
            return {}
        try:
            raw = self.rfile.read(length)
        except socket.timeout as exc:
            raise RequestError(408, "Истекло время чтения запроса.") from exc
        if len(raw) != length:
            raise RequestError(400, "Тело запроса передано не полностью.")
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestError(400, "Некорректный JSON.") from exc
        if not isinstance(data, dict):
            raise RequestError(400, "Корнем JSON должен быть объект.")
        return data

    def _client_key(self) -> str:
        try:
            return str(self.client_address[0])
        except (AttributeError, IndexError, TypeError):
            return "unknown"

    def _session_token(self) -> str:
        header_token = self.headers.get("X-Session", "").strip()
        if header_token:
            return header_token
        raw_cookie = self.headers.get("Cookie", "")
        if not raw_cookie:
            return ""
        cookie = SimpleCookie()
        try:
            cookie.load(raw_cookie)
        except Exception:
            return ""
        morsel = cookie.get(_SESSION_COOKIE)
        return morsel.value if morsel is not None else ""

    def _check_rate(self, limiter: RateLimiter) -> bool:
        allowed, retry_after = limiter.allow(self._client_key())
        if allowed:
            return True
        self._json(
            {"error": "Слишком много запросов. Повторите позже."},
            429,
            extra_headers={"Retry-After": str(retry_after)},
        )
        return False

    def _require_auth(self) -> bool:
        key = self._client_key()
        retry_after = self.auth_limiter.retry_after(key)
        if retry_after:
            self._json(
                {"error": "Слишком много неудачных попыток. Повторите позже."},
                429,
                extra_headers={"Retry-After": str(retry_after)},
            )
            return False
        if self.bridge.authenticate(session=self._session_token()):
            self.auth_limiter.reset(key)
            return True
        allowed, retry_after = self.auth_limiter.allow(key)
        if not allowed:
            self._json(
                {"error": "Слишком много неудачных попыток. Повторите позже."},
                429,
                extra_headers={"Retry-After": str(retry_after)},
            )
        else:
            self._json({"error": "unauthorized"}, 401)
        return False

    def _parsed_path(self) -> str:
        if len(self.path) > MAX_PATH_LENGTH:
            raise RequestError(414, "Слишком длинный адрес запроса.")
        return urlparse(self.path).path

    def _serve_file(
        self,
        path: Path,
        content_type: str,
        *,
        cache_control: str = "public, max-age=86400",
        disposition: str | None = None,
        content_security_policy: str | None = None,
    ) -> None:
        try:
            size = path.stat().st_size
            handle = path.open("rb")
        except OSError:
            self.send_error(404)
            return
        with handle:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            if disposition:
                self.send_header("Content-Disposition", disposition)
            if content_security_policy:
                self.send_header("Content-Security-Policy", content_security_policy)
            self._common_headers(cache_control)
            self.end_headers()
            try:
                shutil.copyfileobj(handle, self.wfile, length=64 * 1024)
            except (BrokenPipeError, ConnectionResetError, socket.timeout):
                pass

    def do_GET(self) -> None:  # noqa: N802
        try:
            path = self._parsed_path()
            if path.startswith("/api/") and not self._check_rate(self.api_limiter):
                return
            if path.startswith("/api/") and self.bridge.shutting_down:
                self._json({"error": "Сервер выключается."}, 503)
                return

            if path in ("/", "/index.html"):
                self._serve_file(
                    _MOBILE_HTML,
                    "text/html; charset=utf-8",
                    cache_control="no-store",
                    content_security_policy=(
                        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                        "connect-src 'self'; object-src 'none'; base-uri 'none'; "
                        "frame-ancestors 'none'"
                    ),
                )
                return

            resources = _MOBILE_HTML.parent
            static_files = {
                "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
                "/icon-180.png": ("icon-180.png", "image/png"),
                "/icon-192.png": ("icon-192.png", "image/png"),
                "/icon-512.png": ("icon-512.png", "image/png"),
                "/favicon.png": ("favicon.png", "image/png"),
                "/mark.svg": ("mark.svg", "image/svg+xml"),
                "/rdev.svg": ("rdev.svg", "image/svg+xml"),
            }
            if path in static_files:
                filename, content_type = static_files[path]
                self._serve_file(resources / filename, content_type)
                return

            if path == "/neyroloc.apk":
                self._serve_file(
                    _ANDROID_APK,
                    "application/vnd.android.package-archive",
                    cache_control="no-store",
                    disposition='attachment; filename="NEYROLOC.apk"',
                )
                return

            if path == "/api/state":
                if not self._require_auth():
                    return
                state = self.bridge.snapshot()
                backend = state["backend"]
                self._json(
                    {
                        "backend": state["backend_name"] or None,
                        "model": getattr(backend, "current_model", None) if backend else None,
                        "models": state["models"],
                        "busy": self.bridge.generation_lock.locked(),
                        "system": state["system"],
                        "temperature": state["temperature"],
                    }
                )
                return

            self.send_error(404)
        except RequestError as exc:
            self._json({"error": exc.message}, exc.status)

    def do_POST(self) -> None:  # noqa: N802
        try:
            path = self._parsed_path()
            if path.startswith("/api/") and not self._check_rate(self.api_limiter):
                return
            if self.bridge.shutting_down:
                self._json({"error": "Сервер выключается."}, 503)
                return

            if path == "/api/pair":
                self._handle_pair()
                return
            if not self._require_auth():
                return
            if path == "/api/model":
                self._handle_model()
                return
            if path == "/api/stop":
                self.bridge.cancel_remote_operation()
                self._json({"ok": True})
                return
            if path == "/api/chat":
                if self._check_rate(self.chat_limiter):
                    self._handle_chat()
                return
            self.send_error(404)
        except RequestError as exc:
            self._json({"error": exc.message}, exc.status)

    def _handle_pair(self) -> None:
        key = self._client_key()
        retry_after = self.auth_limiter.retry_after(key)
        if retry_after:
            self._json(
                {"error": "Слишком много неудачных попыток. Повторите позже."},
                429,
                extra_headers={"Retry-After": str(retry_after)},
            )
            return
        data = self._read_body()
        code = data.get("code")
        ok = isinstance(code, str) and self.bridge.verify_pair_code(code)
        if not ok:
            allowed, retry_after = self.auth_limiter.allow(key)
            if allowed:
                self._json({"ok": False, "error": "Неверный код."}, 401)
            else:
                self._json(
                    {"ok": False, "error": "Слишком много попыток. Повторите позже."},
                    429,
                    extra_headers={"Retry-After": str(retry_after)},
                )
            return

        self.auth_limiter.reset(key)
        token, expires_in = self.bridge.create_session()
        cookie = (
            f"{_SESSION_COOKIE}={token}; Path=/; Max-Age={expires_in}; "
            "HttpOnly; SameSite=Strict"
        )
        self.bridge.statusChanged.emit("Телефон подключился.")
        self._json(
            {"ok": True, "expires_in": expires_in},
            extra_headers={"Set-Cookie": cookie},
        )

    def _handle_model(self) -> None:
        data = self._read_body()
        raw_model = data.get("model")
        if not isinstance(raw_model, str) or not raw_model.strip():
            self._json({"error": "Неизвестная модель."}, 400)
            return
        model = raw_model.strip()
        state = self.bridge.snapshot()
        backend = state["backend"]
        if backend is None:
            self._json({"error": "Backend не подключён на компьютере."}, 409)
            return
        if model not in state["models"]:
            self._json({"error": "Неизвестная модель."}, 400)
            return
        if not self.bridge.generation_lock.acquire(timeout=0.2):
            self._json({"error": "Модель занята — идёт другая операция."}, 409)
            return

        previous_model = backend.current_model
        operation_started = False
        try:
            if not self.bridge.begin_remote_operation(backend):
                self._json({"error": "Backend уже переключён на компьютере."}, 409)
                return
            operation_started = True
            self.bridge.phone_stop.clear()
            backend.set_model(model)
            backend.prepare()
        except Exception as exc:
            try:
                if previous_model:
                    backend.set_model(previous_model)
                else:
                    backend.clear_model()
            except Exception:
                pass
            self.bridge.statusChanged.emit(
                f"Не удалось сменить модель с телефона ({type(exc).__name__})."
            )
            self._json({"error": "Не удалось подготовить модель на компьютере."}, 500)
            return
        finally:
            if operation_started:
                self.bridge.end_remote_operation(backend)
            self.bridge.generation_lock.release()

        self.bridge.modelChanged.emit(model)
        self._json({"ok": True})

    def _validated_chat_request(
        self,
        body: dict[str, Any],
        *,
        default_system: str,
        default_temperature: float,
    ) -> tuple[list[Message], float]:
        raw_messages = body.get("messages")
        if not isinstance(raw_messages, list):
            raise RequestError(400, "Поле messages должно быть списком.")
        if len(raw_messages) > MAX_HISTORY_MESSAGES:
            raise RequestError(
                413,
                f"Слишком длинная история (максимум {MAX_HISTORY_MESSAGES} сообщений).",
            )

        raw_system = body.get("system", default_system)
        if not isinstance(raw_system, str):
            raise RequestError(400, "Системный промпт должен быть строкой.")
        system = raw_system.strip() or default_system
        if len(system) > MAX_SYSTEM_PROMPT_CHARS:
            raise RequestError(413, "Системный промпт слишком большой.")

        raw_temperature = body.get("temperature", default_temperature)
        try:
            temperature = float(raw_temperature)
        except (TypeError, ValueError) as exc:
            raise RequestError(400, "Температура должна быть числом.") from exc
        if not math.isfinite(temperature):
            raise RequestError(400, "Температура должна быть конечным числом.")
        temperature = min(max(temperature, 0.0), 2.0)

        messages: list[Message] = []
        total_chars = len(system)
        if system:
            messages.append(Message("system", system))
        for index, item in enumerate(raw_messages):
            if not isinstance(item, dict):
                raise RequestError(400, f"Сообщение #{index + 1} должно быть объектом.")
            role = item.get("role")
            content = item.get("content")
            if role not in ("user", "assistant"):
                raise RequestError(400, f"Недопустимая роль в сообщении #{index + 1}.")
            if not isinstance(content, str):
                raise RequestError(400, f"Текст сообщения #{index + 1} должен быть строкой.")
            if len(content) > MAX_MESSAGE_CHARS:
                raise RequestError(413, f"Сообщение #{index + 1} слишком большое.")
            total_chars += len(content)
            if total_chars > MAX_TOTAL_MESSAGE_CHARS:
                raise RequestError(413, "Суммарный размер истории слишком большой.")
            if content:
                messages.append(Message(role, content))
        if not messages or messages[-1].role != "user":
            raise RequestError(400, "Пустое сообщение.")
        return messages, temperature

    def _handle_chat(self) -> None:
        state = self.bridge.snapshot()
        backend = state["backend"]
        if backend is None:
            self._json({"error": "Backend не подключён на компьютере."}, 409)
            return
        if not getattr(backend, "current_model", None):
            self._json({"error": "Модель не выбрана."}, 409)
            return

        body = self._read_body()
        messages, temperature = self._validated_chat_request(
            body,
            default_system=state["system"],
            default_temperature=state["temperature"],
        )
        if not self.bridge.generation_lock.acquire(timeout=0.2):
            self._json({"error": "Модель занята — идёт другая генерация."}, 409)
            return

        operation_started = False
        generator = None
        response_started = False
        stopped = False
        try:
            if not self.bridge.begin_remote_operation(backend):
                self._json({"error": "Backend уже переключён на компьютере."}, 409)
                return
            operation_started = True
            self.bridge.phone_stop.clear()
            self.bridge.statusChanged.emit("Генерация по запросу с телефона…")

            generator = backend.generate(messages, temperature)
            try:
                first_piece = next(generator)
            except StopIteration:
                first_piece = None
            except Exception as exc:
                self.bridge.statusChanged.emit(
                    f"Ошибка генерации с телефона ({type(exc).__name__})."
                )
                self._json({"error": "Не удалось запустить генерацию."}, 502)
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._common_headers("no-store")
            self.end_headers()
            response_started = True

            sent_bytes = 0
            if first_piece is not None and not self.bridge.phone_stop.is_set():
                encoded = str(first_piece).encode("utf-8")
                if len(encoded) > MAX_STREAM_RESPONSE_BYTES:
                    stopped = True
                    backend.cancel()
                else:
                    self.wfile.write(encoded)
                    self.wfile.flush()
                    sent_bytes += len(encoded)
            elif self.bridge.phone_stop.is_set():
                stopped = True

            if first_piece is not None and not stopped:
                for piece in generator:
                    if self.bridge.phone_stop.is_set():
                        stopped = True
                        break
                    encoded = str(piece).encode("utf-8")
                    if sent_bytes + len(encoded) > MAX_STREAM_RESPONSE_BYTES:
                        stopped = True
                        backend.cancel()
                        break
                    self.wfile.write(encoded)
                    self.wfile.flush()
                    sent_bytes += len(encoded)
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            stopped = True
            backend.cancel()
        except Exception as exc:
            self.bridge.statusChanged.emit(
                f"Ошибка генерации с телефона ({type(exc).__name__})."
            )
            if response_started:
                try:
                    self.wfile.write(
                        "\n\n[Ошибка генерации. Подробности доступны на компьютере.]".encode(
                            "utf-8"
                        )
                    )
                except OSError:
                    pass
            else:
                self._json({"error": "Ошибка генерации."}, 502)
        finally:
            if generator is not None:
                try:
                    generator.close()
                except Exception:
                    pass
            if operation_started:
                self.bridge.end_remote_operation(backend)
            self.bridge.generation_lock.release()
            self.bridge.statusChanged.emit(
                "Остановлено (запрос с телефона)."
                if stopped or self.bridge.phone_stop.is_set()
                else "Готово (запрос с телефона)."
            )


class _BoundedThreadingHTTPServer(ThreadingHTTPServer):
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


class RemoteServer:
    """Обёртка над bounded ThreadingHTTPServer с корректным lifecycle."""

    def __init__(self, bridge: RemoteBridge, port: int = DEFAULT_PORT) -> None:
        if not 0 <= int(port) <= 65_535:
            raise ValueError("Некорректный TCP-порт.")
        self.bridge = bridge
        self._bind_port = int(port)
        self.port = int(port)
        self._httpd: _BoundedThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._lifecycle_lock = threading.RLock()

    @property
    def running(self) -> bool:
        with self._lifecycle_lock:
            return self._httpd is not None and self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        with self._lifecycle_lock:
            if self._httpd is not None:
                return
            handler = type(
                "BoundHandler",
                (_Handler,),
                {
                    "bridge": self.bridge,
                    "auth_limiter": RateLimiter(
                        AUTH_FAILURE_LIMIT,
                        AUTH_FAILURE_WINDOW_SECONDS,
                    ),
                    "api_limiter": RateLimiter(
                        API_REQUEST_LIMIT,
                        API_REQUEST_WINDOW_SECONDS,
                    ),
                    "chat_limiter": RateLimiter(
                        CHAT_REQUEST_LIMIT,
                        CHAT_REQUEST_WINDOW_SECONDS,
                    ),
                },
            )
            httpd = _BoundedThreadingHTTPServer(("0.0.0.0", self._bind_port), handler)
            thread = threading.Thread(
                target=httpd.serve_forever,
                name="neyroloc-remote-server",
                daemon=True,
            )
            self.bridge.end_shutdown()
            try:
                thread.start()
            except BaseException:
                httpd.server_close()
                self.bridge.begin_shutdown()
                raise
            self._httpd = httpd
            self._thread = thread
            self.port = int(httpd.server_address[1])

    def stop(self) -> None:
        with self._lifecycle_lock:
            httpd = self._httpd
            thread = self._thread
            if httpd is None:
                self.bridge.begin_shutdown()
                return
            self.bridge.begin_shutdown()
            httpd.shutdown()
            httpd.server_close()
            if thread is not None and thread is not threading.current_thread():
                thread.join(timeout=2.0)

            # Wait only for a phone-owned operation. A desktop generation uses
            # the same lock but must not be cancelled merely because access was
            # switched off in the dialog.
            if self.bridge.has_active_remote_operation:
                acquired = self.bridge.generation_lock.acquire(timeout=3.0)
                if acquired:
                    self.bridge.generation_lock.release()
            self._httpd = None
            self._thread = None
