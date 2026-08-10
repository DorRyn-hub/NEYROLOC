from __future__ import annotations

import io
import json
import sys
import types
import unittest
from http.cookies import SimpleCookie
from email.message import Message as HeaderMessage
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "NEYROLOCK_5"
sys.path.insert(0, str(APP_ROOT))

# The HTTP/core tests must also run with a plain Python installation.  A tiny
# QtCore compatibility stub is enough because no QApplication or GUI is used.
try:
    import PySide6.QtCore  # noqa: F401
except ModuleNotFoundError:
    pyside = types.ModuleType("PySide6")
    qtcore = types.ModuleType("PySide6.QtCore")

    class QObject:
        pass

    class Signal:
        def __init__(self, *args) -> None:
            self.emissions: list[tuple] = []

        def emit(self, *args) -> None:
            self.emissions.append(args)

    qtcore.QObject = QObject
    qtcore.Signal = Signal
    pyside.QtCore = qtcore
    sys.modules["PySide6"] = pyside
    sys.modules["PySide6.QtCore"] = qtcore

from core import remote_server  # noqa: E402


class RemoteServerCoreTests(unittest.TestCase):
    def handler(self, bridge=None, body: bytes = b""):
        handler = remote_server._Handler.__new__(remote_server._Handler)
        handler.bridge = bridge or remote_server.RemoteBridge()
        handler.headers = HeaderMessage()
        handler.headers["Content-Length"] = str(len(body))
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.client_address = ("127.0.0.1", 12345)
        handler.path = "/"
        handler.auth_limiter = remote_server.RateLimiter(8, 60)
        handler.api_limiter = remote_server.RateLimiter(120, 60)
        handler.chat_limiter = remote_server.RateLimiter(12, 60)
        handler.replies: list[tuple[int, dict, dict]] = []

        def reply(payload, status=200, *, extra_headers=None):
            handler.replies.append((status, payload, extra_headers or {}))

        handler._json = reply
        handler.send_error = lambda status, *args, **kwargs: handler.replies.append(
            (status, {"error": "send_error"}, {})
        )
        return handler

    def test_lan_detection_is_total_for_malformed_input(self) -> None:
        self.assertTrue(remote_server._looks_lan("192.168.1.2"))
        self.assertTrue(remote_server._looks_lan("172.16.0.1"))
        self.assertFalse(remote_server._looks_lan("172.bad"))
        self.assertFalse(remote_server._looks_lan("100.64.0.1"))
        self.assertFalse(remote_server._looks_lan("2001:db8::1"))

    def test_body_parser_rejects_malformed_oversize_and_non_object_json(self) -> None:
        valid = self.handler(body=b'{"ok":true}')
        self.assertEqual(valid._read_body(), {"ok": True})

        invalid_length = self.handler()
        invalid_length.headers.replace_header("Content-Length", "bad")
        with self.assertRaises(remote_server.RequestError) as caught:
            invalid_length._read_body()
        self.assertEqual(caught.exception.status, 400)

        with mock.patch.object(remote_server, "MAX_REQUEST_BODY_BYTES", 4):
            with self.assertRaises(remote_server.RequestError) as caught:
                self.handler(body=b"12345")._read_body()
        self.assertEqual(caught.exception.status, 413)

        with self.assertRaises(remote_server.RequestError):
            self.handler(body=b"[]")._read_body()
        truncated = self.handler(body=b"{}")
        truncated.headers.replace_header("Content-Length", "3")
        with self.assertRaises(remote_server.RequestError):
            truncated._read_body()

    def test_pair_creates_session_and_pair_code_rotation_revokes_it(self) -> None:
        bridge = remote_server.RemoteBridge()
        bridge.pair_code = "123456"
        body = json.dumps({"code": "123456"}).encode("utf-8")
        handler = self.handler(bridge, body)

        handler._handle_pair()

        status, payload, headers = handler.replies[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertNotIn("session", payload)
        cookie = SimpleCookie()
        cookie.load(headers["Set-Cookie"])
        token = cookie["neyroloc_session"].value
        self.assertTrue(bridge.validate_session(token))
        bridge.pair_code = "654321"
        self.assertFalse(bridge.validate_session(token))

    def test_state_requires_auth_and_accepts_pair_session(self) -> None:
        bridge = remote_server.RemoteBridge()
        bridge.pair_code = "123456"
        bridge.backend_name = "Local GGUF"
        bridge.available_models = ["model.gguf"]

        unauthorized = self.handler(bridge)
        unauthorized.path = "/api/state"
        unauthorized.do_GET()
        self.assertEqual(unauthorized.replies[-1][0], 401)

        token, _ = bridge.create_session()
        authorized = self.handler(bridge)
        authorized.path = "/api/state?ignored=1"
        authorized.headers["X-Session"] = token
        authorized.do_GET()
        status, payload, _ = authorized.replies[-1]
        self.assertEqual(status, 200)
        self.assertEqual(payload["backend"], "Local GGUF")
        self.assertEqual(payload["models"], ["model.gguf"])
        self.assertFalse(payload["busy"])

    def test_pair_code_cannot_be_reused_as_permanent_api_token(self) -> None:
        bridge = remote_server.RemoteBridge()
        bridge.pair_code = "123456"
        handler = self.handler(bridge)
        handler.path = "/api/state"
        handler.headers["X-Code"] = "123456"

        handler.do_GET()

        self.assertEqual(handler.replies[-1][0], 401)

    def test_chat_validation_needs_user_tail_and_bounds_temperature(self) -> None:
        handler = self.handler()
        messages, temperature = handler._validated_chat_request(
            {"messages": [{"role": "user", "content": "Привет"}], "temperature": 9},
            default_system="",
            default_temperature=0.7,
        )
        self.assertEqual(messages[-1].content, "Привет")
        self.assertEqual(temperature, 2.0)

        with self.assertRaises(remote_server.RequestError):
            handler._validated_chat_request(
                {"messages": [{"role": "assistant", "content": "Нет user"}]},
                default_system="",
                default_temperature=0.7,
            )


if __name__ == "__main__":
    unittest.main()
