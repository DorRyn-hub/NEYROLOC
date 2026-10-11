"""Удалённый доступ с телефона: HTTP-сервер внутри настольного приложения.

Телефон в той же Wi-Fi-сети открывает http://<ip-компа>:8765, вводит код
сопряжения (показан в диалоге на компе) и получает мобильный чат-интерфейс,
который управляет тем же backend'ом, что подключён в настольном приложении.

Реализовано на stdlib (ThreadingHTTPServer) — без новых зависимостей.
Каждый запрос обрабатывается в своём потоке; генерация защищена общим
`generation_lock`, чтобы телефон и десктоп не дёргали одну модель
одновременно (llama.cpp этого не переживёт).
"""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Signal

from backends.base import Message

DEFAULT_PORT = 8765
_MOBILE_HTML = Path(__file__).resolve().parent.parent / "resources" / "mobile.html"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _looks_lan(ip: str) -> bool:
    """Настоящий адрес домашней сети, а не VPN-туннель.

    UDP-трюк с 8.8.8.8 при активном VPN возвращает адрес туннеля
    (например 198.18.0.1 у Karing или 100.x.x.x у Tailscale) — телефон
    в той же Wi-Fi-сети по нему не подключится.
    """
    return ip.startswith(("192.168.", "10.")) or (
        ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31
    )


def local_ip() -> str:
    """IP этого компьютера в локальной Wi-Fi-сети."""
    # Сначала — реальные интерфейсы (en0 = Wi-Fi на Mac).
    import subprocess

    for iface in ("en0", "en1", "en2"):
        try:
            out = subprocess.run(
                ["ipconfig", "getifaddr", iface],
                capture_output=True, text=True, timeout=3,
            ).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out and _looks_lan(out):
            return out

    # Фолбэк: UDP-трюк (может вернуть адрес VPN-туннеля, но лучше, чем ничего).
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def tailscale_ip() -> str | None:
    """Tailscale-адрес этого Mac (100.x.x.x) — доступ откуда угодно, вне Wi-Fi.

    Возвращает None, если Tailscale не установлен/не запущен. Сервер слушает
    0.0.0.0, поэтому по этому адресу он доступен из любой сети, где телефон
    тоже в том же tailnet — без проброса портов и без общей Wi-Fi.
    """
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
                capture_output=True, text=True, timeout=4,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out.returncode == 0:
            ip = out.stdout.strip().splitlines()[0].strip() if out.stdout.strip() else ""
            if ip.startswith("100."):
                return ip
    return None


class RemoteBridge(QObject):
    """Потокобезопасный мост между HTTP-потоками и Qt-приложением.

    HTTP-обработчики читают только простые python-атрибуты и объект backend
    (генерация — чистый python, Qt не трогается). Обо всех событиях UI
    узнаёт через сигналы — они безопасно доставляются в главный поток.
    """

    statusChanged = Signal(str)
    modelChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.generation_lock = threading.Lock()
        self.phone_stop = threading.Event()
        # Обновляется главным потоком (MainWindow), читается HTTP-потоками.
        self.backend = None
        self.backend_name: str = ""
        self.available_models: list[str] = []
        self.system_prompt: str = ""
        self.temperature: float = 0.7
        self.pair_code: str = ""


class _Handler(BaseHTTPRequestHandler):
    # Устанавливается фабрикой в RemoteServer.
    bridge: RemoteBridge = None  # type: ignore[assignment]

    # ----- инфраструктура -----

    def log_message(self, *args) -> None:  # noqa: D401 — не спамить в stdout
        pass

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _authed(self) -> bool:
        return self.headers.get("X-Code", "") == self.bridge.pair_code

    # ----- маршруты -----

    def _serve_static(self, path: Path, content_type: str) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 — stdlib API
        # Ссылка из QR-кода приходит с параметром (…/?code=123456) — сравниваем
        # только путь, иначе ни один маршрут не совпадёт.
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            try:
                body = _MOBILE_HTML.read_bytes()
            except OSError:
                self.send_error(500, "mobile.html not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Статика для PWA («На экран Домой» → приложение с иконкой на телефоне).
        _RES = _MOBILE_HTML.parent
        if path == "/manifest.webmanifest":
            self._serve_static(_RES / "manifest.webmanifest", "application/manifest+json")
            return
        if path in ("/icon-180.png", "/icon-192.png", "/icon-512.png", "/favicon.png"):
            self._serve_static(_RES / path.lstrip("/"), "image/png")
            return
        if path in ("/mark.svg", "/rdev.svg"):
            self._serve_static(_RES / path.lstrip("/"), "image/svg+xml")
            return

        if path == "/neyroloc.apk":
            # Установочный файл Android-приложения — скачивается браузером
            # телефона прямо с этого сервера, USB не нужен.
            apk = _PROJECT_ROOT / "packaging" / "android" / "NEYROLOC.apk"
            try:
                body = apk.read_bytes()
            except OSError:
                self.send_error(404, "APK not built")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.android.package-archive")
            self.send_header("Content-Disposition", 'attachment; filename="NEYROLOC.apk"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/state":
            if not self._authed():
                self._json({"error": "unauthorized"}, 401)
                return
            b = self.bridge
            self._json(
                {
                    "backend": b.backend_name or None,
                    "model": getattr(b.backend, "current_model", None) if b.backend else None,
                    "models": b.available_models,
                    "busy": b.generation_lock.locked(),
                    # Значения с компьютера — телефон показывает их как значения
                    # по умолчанию и может переопределить для своего запроса.
                    "system": b.system_prompt,
                    "temperature": b.temperature,
                }
            )
            return

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 — stdlib API
        if self.path == "/api/pair":
            data = self._read_body()
            ok = data.get("code", "") == self.bridge.pair_code
            if ok:
                self.bridge.statusChanged.emit("Телефон подключился.")
            self._json({"ok": ok}, 200 if ok else 401)
            return

        if not self._authed():
            self._json({"error": "unauthorized"}, 401)
            return

        if self.path == "/api/model":
            model = str(self._read_body().get("model", "")).strip()
            b = self.bridge
            if b.backend is None:
                self._json({"error": "Backend не подключён на компьютере."}, 409)
                return
            if model and model in b.available_models:
                b.backend.set_model(model)
                b.modelChanged.emit(model)
                self._json({"ok": True})
            else:
                self._json({"error": "Неизвестная модель."}, 400)
            return

        if self.path == "/api/stop":
            self.bridge.phone_stop.set()
            self._json({"ok": True})
            return

        if self.path == "/api/chat":
            self._handle_chat()
            return

        self.send_error(404)

    # ----- генерация -----

    def _handle_chat(self) -> None:
        b = self.bridge
        if b.backend is None:
            self._json({"error": "Backend не подключён на компьютере."}, 409)
            return
        if not getattr(b.backend, "current_model", None):
            self._json({"error": "Модель не выбрана."}, 409)
            return

        body = self._read_body()
        raw = body.get("messages", [])

        # Телефон может переопределить системный промпт и температуру только
        # для своего запроса — состояние компьютера при этом не меняется
        # (сервер остаётся stateless).
        system = str(body.get("system", "")).strip() or b.system_prompt
        try:
            temperature = float(body["temperature"])
        except (KeyError, TypeError, ValueError):
            temperature = b.temperature
        temperature = min(max(temperature, 0.0), 2.0)

        messages: list[Message] = []
        if system:
            messages.append(Message("system", system))
        for m in raw:
            role = m.get("role")
            content = str(m.get("content", ""))
            if role in ("user", "assistant") and content:
                messages.append(Message(role, content))
        if not messages or messages[-1].role != "user":
            self._json({"error": "Пустое сообщение."}, 400)
            return

        if not b.generation_lock.acquire(timeout=0.2):
            self._json({"error": "Модель занята — идёт другая генерация."}, 409)
            return

        b.phone_stop.clear()
        b.statusChanged.emit("Генерация по запросу с телефона…")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            # Без Content-Length: поток до закрытия соединения (HTTP/1.0).
            self.end_headers()
            gen = b.backend.generate(messages, temperature)
            try:
                for piece in gen:
                    if b.phone_stop.is_set():
                        break
                    try:
                        self.wfile.write(piece.encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break  # телефон закрыл страницу
            finally:
                gen.close()
        except Exception as exc:  # noqa: BLE001 — ошибку показываем на телефоне
            try:
                self.wfile.write(f"\n\n[Ошибка: {exc}]".encode("utf-8"))
            except OSError:
                pass
        finally:
            b.generation_lock.release()
            b.statusChanged.emit("Готово (запрос с телефона).")


class RemoteServer:
    """Обёртка над ThreadingHTTPServer с фоновым потоком."""

    def __init__(self, bridge: RemoteBridge, port: int = DEFAULT_PORT) -> None:
        self.bridge = bridge
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._httpd is not None

    def start(self) -> None:
        if self._httpd is not None:
            return
        handler = type("BoundHandler", (_Handler,), {"bridge": self.bridge})
        self._httpd = ThreadingHTTPServer(("0.0.0.0", self.port), handler)
        self._httpd.daemon_threads = True
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        self._httpd = None
        self._thread = None
