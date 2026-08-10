from __future__ import annotations

import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BROKER_PATH = PROJECT_ROOT / "deploy" / "broker.py"


class BrokerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.environment = mock.patch.dict(
            os.environ,
            {
                "NEYROLOC_BASE_DOMAIN": "neyroloc.example.test",
                "NEYROLOC_REGISTRY": str(Path(cls.temporary.name) / "registry.json"),
                "NEYROLOC_FRPS_TOKEN_FILE": str(Path(cls.temporary.name) / "token"),
            },
        )
        cls.environment.start()
        spec = importlib.util.spec_from_file_location("neyroloc_test_broker", BROKER_PATH)
        assert spec is not None and spec.loader is not None
        cls.broker = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.broker
        spec.loader.exec_module(cls.broker)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("neyroloc_test_broker", None)
        cls.environment.stop()
        cls.temporary.cleanup()

    def handler(self, body: bytes = b""):
        handler = self.broker.Handler.__new__(self.broker.Handler)
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.client_address = ("127.0.0.1", 12345)
        handler.close_connection = False
        return handler

    def test_body_parser_accepts_object_and_rejects_bad_inputs(self) -> None:
        self.assertEqual(self.handler(b'{"name":"device"}')._body(), {"name": "device"})

        invalid_length = self.handler()
        invalid_length.headers["Content-Length"] = "invalid"
        with self.assertRaises(self.broker.RequestBodyError) as caught:
            invalid_length._body()
        self.assertEqual(caught.exception.status, 400)

        with self.assertRaises(self.broker.RequestBodyError):
            self.handler(b"[]")._body()
        with mock.patch.object(self.broker, "MAX_REQUEST_BODY_BYTES", 4):
            with self.assertRaises(self.broker.RequestBodyError) as caught:
                self.handler(b"12345")._body()
        self.assertEqual(caught.exception.status, 413)

    def test_body_error_is_returned_as_json_and_closes_connection(self) -> None:
        handler = self.handler(b"not-json")
        replies: list[tuple[int, dict]] = []
        handler._json = lambda payload, status=200: replies.append((status, payload))

        self.assertIsNone(handler._read_json_or_reply())
        self.assertEqual(replies[0][0], 400)
        self.assertTrue(handler.close_connection)

    def test_forwarded_ip_is_trusted_only_from_loopback(self) -> None:
        handler = self.handler()
        handler.headers["X-Forwarded-For"] = "203.0.113.4, 127.0.0.1"
        self.assertEqual(handler._client_ip(), "203.0.113.4")

        handler.client_address = ("198.51.100.7", 12345)
        self.assertEqual(handler._client_ip(), "198.51.100.7")

        handler.client_address = ("127.0.0.1", 12345)
        handler.headers["X-Forwarded-For"] = "not-an-ip"
        self.assertEqual(handler._client_ip(), "127.0.0.1")

    def test_frps_login_proxy_ownership_and_unknown_operation(self) -> None:
        entry = self.broker.registry.create("test device")
        user = entry["subdomain"]
        handler = self.handler()
        replies: list[tuple[int, dict]] = []
        handler._json = lambda payload, status=200: replies.append((status, payload))

        handler._handle_frps(
            {"op": "Login", "content": {"user": user, "metas": {"secret": entry["secret"]}}}
        )
        self.assertEqual(replies.pop()[1], {"unchange": True})

        handler._handle_frps(
            {"op": "NewProxy", "content": {"user": {"user": user}, "subdomain": "other"}}
        )
        self.assertTrue(replies.pop()[1]["reject"])

        handler._handle_frps({"op": "Unexpected", "content": {}})
        unknown = replies.pop()[1]
        self.assertTrue(unknown["reject"])
        self.assertEqual(unknown["reject_reason"], "unsupported operation")

    def test_registry_fails_closed_on_wrong_json_shape(self) -> None:
        path = Path(self.temporary.name) / "wrong-shape.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.broker.Registry(path)

    def test_registry_write_is_private_and_round_trips(self) -> None:
        path = Path(self.temporary.name) / "private-registry.json"
        registry = self.broker.Registry(path)
        created = registry.create("test device")
        restored = self.broker.Registry(path)
        self.assertEqual(restored.get(created["subdomain"])["secret"], created["secret"])
        self.assertEqual(path.stat().st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
