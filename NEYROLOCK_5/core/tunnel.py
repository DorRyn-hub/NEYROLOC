"""Публичный доступ к телефону через FRP-туннель.

Локальный HTTP-сервер (core/remote_server.py) виден только в своей Wi-Fi-сети.
Чтобы телефон работал из любой сети, компьютер поднимает исходящий туннель к
своему VPS: `frpc` соединяется с `frps`, а тот проксирует публичный HTTPS-адрес
на localhost:8765. Никаких проброшенных портов и белого IP не требуется.

Здесь — управление дочерним процессом frpc: конфиг, запуск, чтение логов,
остановка. Qt-виджеты о процессе ничего не знают, общение через сигналы.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from core.config import CONFIG_DIR
from core.json_store import atomic_write_text


# Куда кладём сгенерированный конфиг frpc (в нём токен — права 0600).
FRPC_CONFIG = CONFIG_DIR / "frpc.toml"

# Сервис, выдающий каждому компьютеру личный поддомен. Единственный адрес,
# который приложению нужно знать заранее: адрес сервера, токены и поддомен
# приходят от него при регистрации.
BROKER_URL = "https://neyroloc.static-assets-io.website"

# Строки в выводе frpc, по которым понимаем, что произошло.
_OK_MARKERS = ("start proxy success",)
_LOGIN_FAIL = ("login to server failed", "connect to server error")
MAX_BROKER_RESPONSE_BYTES = 64 * 1024


def _toml_string(value) -> str:
    """Quote an untrusted broker/config value as a TOML basic string."""
    return json.dumps(str(value), ensure_ascii=False)


class Tunnel(QObject):
    """Обёртка над процессом frpc."""

    statusChanged = Signal(str)          # человекочитаемый статус для UI
    runningChanged = Signal(bool)        # включился/выключился

    def __init__(self, config, local_port: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._local_port = local_port
        self._proc: subprocess.Popen | None = None
        self._reader: threading.Thread | None = None
        self._stopping = False

    # ----- настройки -----

    @property
    def settings(self) -> dict:
        settings = self._config.data.get("tunnel", {})
        return settings if isinstance(settings, dict) else {}

    @property
    def configured(self) -> bool:
        s = self.settings
        # secret — признак нового (мульти-тенантного) формата: он выдаётся
        # брокером вместе с личным поддоменом.
        return bool(
            s.get("server") and s.get("token") and s.get("subdomain")
            and s.get("domain") and s.get("secret")
        )

    def provision(self, device_name: str = "") -> bool:
        """Получить у брокера личный поддомен и параметры подключения.

        Вызывается один раз: результат сохраняется в config.json и дальше
        используется как есть.
        """
        if self.configured:
            return True
        self.statusChanged.emit("Получаем личный адрес…")
        payload = json.dumps({"name": device_name or "desktop"}).encode("utf-8")
        request = urllib.request.Request(
            f"{BROKER_URL}/api/register",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read(MAX_BROKER_RESPONSE_BYTES + 1)
                if len(raw) > MAX_BROKER_RESPONSE_BYTES:
                    raise ValueError("ответ брокера слишком большой")
                data = json.loads(raw.decode("utf-8"))
        except (
            urllib.error.URLError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            self.statusChanged.emit(f"Не удалось получить адрес: {exc}")
            return False

        required = ("subdomain", "secret", "domain", "server", "frps_token")
        if not isinstance(data, dict) or not all(data.get(k) for k in required):
            self.statusChanged.emit("Сервер вернул неполный ответ регистрации.")
            return False
        try:
            port = int(data.get("port", 7000))
        except (TypeError, ValueError):
            port = 0
        text_values = [str(data[key]) for key in required]
        if not 1 <= port <= 65_535 or any(
            len(value) > 4_096 or any(ord(char) < 32 for char in value)
            for value in text_values
        ):
            self.statusChanged.emit("Сервер вернул некорректные параметры регистрации.")
            return False

        self._config.data["tunnel"] = {
            "server": data["server"],
            "port": port,
            "token": data["frps_token"],
            "secret": data["secret"],
            "subdomain": data["subdomain"],
            "domain": data["domain"],
        }
        if not self._config.save():
            self.statusChanged.emit("Не удалось сохранить параметры туннеля.")
            return False
        self.statusChanged.emit(f"Личный адрес получен: {self.public_url}")
        return True

    @property
    def public_url(self) -> str:
        s = self.settings
        if not (s.get("subdomain") and s.get("domain")):
            return ""
        return f"https://{s['subdomain']}.{s['domain']}"

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # ----- бинарник -----

    def find_binary(self) -> Path | None:
        """frpc: путь из настроек, рядом с приложением, в проекте или в PATH."""
        candidates: list[Path] = []
        custom = self.settings.get("frpc_path")
        if custom:
            candidates.append(Path(custom).expanduser())

        here = Path(__file__).resolve().parent.parent          # …/NEYROLOCK_5
        executable_root = Path(sys.executable).resolve().parent
        candidates += [
            here / "resources" / "bin" / "frpc",               # рядом с приложением
            executable_root / "resources" / "bin" / "frpc",
            executable_root.parent / "Resources" / "resources" / "bin" / "frpc",
            here.parent / "remote" / "frpc-darwin-arm64",      # в репозитории
            CONFIG_DIR / "bin" / "frpc",
        ]
        found = shutil.which("frpc")
        if found:
            candidates.append(Path(found))

        for path in candidates:
            try:
                if path.is_file():
                    return path
            except OSError:
                continue
        return None

    # ----- конфиг -----

    def _write_config(self) -> Path:
        s = self.settings
        try:
            server_port = int(s.get("port", 7000))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Некорректный порт сервера туннеля.") from exc
        if not 1 <= server_port <= 65_535 or not 1 <= int(self._local_port) <= 65_535:
            raise RuntimeError("Некорректный порт туннеля.")
        text = (
            f"serverAddr = {_toml_string(s['server'])}\n"
            f"serverPort = {server_port}\n"
            "loginFailExit = false\n"
            'auth.method = "token"\n'
            f"auth.token = {_toml_string(s['token'])}\n"
            # user + secret: по ним сервер узнаёт арендатора и пускает его
            # только на собственный поддомен.
            f"user = {_toml_string(s['subdomain'])}\n"
            f"metadatas.secret = {_toml_string(s['secret'])}\n"
            "\n"
            "[[proxies]]\n"
            'name = "neyroloc"\n'
            'type = "http"\n'
            'localIP = "127.0.0.1"\n'
            f"localPort = {self._local_port}\n"
            f"subdomain = {_toml_string(s['subdomain'])}\n"
        )
        atomic_write_text(FRPC_CONFIG, text, mode=0o600)
        return FRPC_CONFIG

    # ----- запуск/остановка -----

    def start(self) -> bool:
        if self.running:
            return True
        # Первый запуск (или конфиг старого формата) — регистрируемся сами.
        if not self.configured and not self.provision():
            return False

        binary = self.find_binary()
        if binary is None:
            self.statusChanged.emit("Не найден frpc — положите его в resources/bin/frpc.")
            return False

        try:
            config_path = self._write_config()
            self._stopping = False
            self._proc = subprocess.Popen(
                [str(binary), "-c", str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            self._proc = None
            self.statusChanged.emit(f"Не удалось запустить туннель: {exc}")
            return False

        self._reader = threading.Thread(target=self._read_output, daemon=True)
        self._reader.start()
        self.statusChanged.emit("Туннель запускается…")
        self.runningChanged.emit(True)
        return True

    def _read_output(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        for line in proc.stdout:
            low = line.lower()
            if any(m in low for m in _OK_MARKERS):
                self.statusChanged.emit(f"Публичный адрес работает: {self.public_url}")
            elif any(m in low for m in _LOGIN_FAIL):
                self.statusChanged.emit("Сервер туннеля недоступен — пробуем ещё раз…")
        # Процесс завершился.
        if not self._stopping:
            self.statusChanged.emit("Туннель остановлен.")
            self.runningChanged.emit(False)

    def stop(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None or proc.poll() is not None:
            self.runningChanged.emit(False)
            return
        self._stopping = True
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        except OSError:
            pass
        self.statusChanged.emit("Публичный доступ выключен.")
        self.runningChanged.emit(False)
