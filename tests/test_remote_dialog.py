from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "NEYROLOCK_5"
sys.path.insert(0, str(APP_ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, Signal
    from PySide6.QtWidgets import QApplication, QWidget

    from ui.remote_dialog import RemoteAccessDialog
except (ImportError, ModuleNotFoundError):
    UI_AVAILABLE = False
else:
    UI_AVAILABLE = True


if UI_AVAILABLE:

    class _FakeTunnel(QObject):
        statusChanged = Signal(str)
        runningChanged = Signal(bool)
        stateChanged = Signal(str)

        def __init__(self) -> None:
            super().__init__()
            self.running = True
            self.requested = True
            self.ready = False
            self.state = "retrying"
            self.public_url = "https://device.example.invalid"
            self.last_status = "Повторяем подключение автоматически…"
            self.start_result = True
            self.stop_calls = 0

        def start(self) -> bool:
            if not self.start_result:
                self.requested = False
                self.state = "error"
                self.last_status = "Не удалось запустить туннель."
                self.statusChanged.emit(self.last_status)
            return self.start_result

        def stop(self) -> None:
            self.stop_calls += 1
            self.requested = False
            self.running = False
            self.ready = False
            self.state = "off"
            self.runningChanged.emit(False)


@unittest.skipUnless(UI_AVAILABLE, "PySide6 is required for remote dialog tests")
class RemoteDialogStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.local_running = True
        self.tunnel = _FakeTunnel()
        self.dialog = RemoteAccessDialog(
            is_running=lambda: self.local_running,
            start=lambda: None,
            stop=lambda: None,
            lan_url="http://192.168.1.10:8765",
            pair_code="123456",
            tunnel=self.tunnel,
        )
        self.addCleanup(self.dialog.close)

    def test_retrying_public_tunnel_hides_misleading_lan_qr(self) -> None:
        target, caption = self.dialog._qr_target()
        self.assertEqual(target, "")
        self.assertIn("ещё проверяется", caption)
        self.assertFalse(self.dialog._qr_label.isVisible())
        self.assertIn("Локальный сервер работает", self.dialog._state_label.text())
        self.assertIn("восстанавливается автоматически", self.dialog._state_label.text())
        self.assertNotIn("Публичный сервер недоступен", self.dialog._state_label.text())
        self.assertTrue(self.dialog._tunnel_check.isChecked())

    def test_online_tunnel_switches_qr_to_public_url(self) -> None:
        self.tunnel.ready = True
        self.tunnel.state = "online"
        self.tunnel.stateChanged.emit("online")
        target, _caption = self.dialog._qr_target()
        self.assertTrue(target.startswith(self.tunnel.public_url + "/"))
        self.assertIn("публичный адрес работают", self.dialog._state_label.text())

    def test_process_exit_unchecks_public_access(self) -> None:
        self.tunnel.running = False
        self.tunnel.requested = False
        self.tunnel.runningChanged.emit(False)
        self.assertFalse(self.dialog._tunnel_check.isChecked())

    def test_start_failure_preserves_error_and_does_not_call_stop(self) -> None:
        self.dialog.close()
        self.tunnel.running = False
        self.tunnel.requested = False
        self.tunnel.state = "off"
        self.tunnel.start_result = False
        self.dialog = RemoteAccessDialog(
            is_running=lambda: self.local_running,
            start=lambda: None,
            stop=lambda: None,
            lan_url="http://192.168.1.10:8765",
            pair_code="123456",
            tunnel=self.tunnel,
        )
        self.addCleanup(self.dialog.close)
        self.dialog._tunnel_check.setChecked(True)

        self.assertFalse(self.dialog._tunnel_check.isChecked())
        self.assertEqual(self.tunnel.stop_calls, 0)
        self.assertEqual(self.tunnel.state, "error")
        self.assertIn("Не удалось", self.dialog._tunnel_state.text())
        self.assertIn("требует внимания", self.dialog._state_label.text())

    def test_local_server_start_error_is_not_overwritten_by_tunnel_stop(self) -> None:
        self.dialog.close()
        self.local_running = False
        self.tunnel.running = False
        self.tunnel.requested = False
        self.tunnel.state = "off"

        def fail_local_start() -> None:
            raise OSError(48, "Address already in use")

        self.dialog = RemoteAccessDialog(
            is_running=lambda: self.local_running,
            start=fail_local_start,
            stop=lambda: None,
            lan_url="http://192.168.1.10:8765",
            pair_code="123456",
            tunnel=self.tunnel,
        )
        self.addCleanup(self.dialog.close)
        self.dialog._tunnel_check.setChecked(True)

        self.assertFalse(self.dialog._tunnel_check.isChecked())
        self.assertEqual(self.tunnel.stop_calls, 0)
        self.assertIn("Порт 8765 занят", self.dialog._state_label.text())

    def test_stale_status_payload_renders_authoritative_snapshot(self) -> None:
        self.tunnel.running = False
        self.tunnel.requested = False
        self.tunnel.ready = False
        self.tunnel.state = "off"
        self.tunnel.last_status = "Публичный доступ выключен."

        self.dialog._on_tunnel_status("Публичный адрес проверен и работает")

        self.assertEqual(
            self.dialog._tunnel_state.text(),
            "Публичный доступ выключен.",
        )
        self.assertFalse(self.dialog._tunnel_check.isChecked())

    def test_public_qr_requires_local_server_too(self) -> None:
        self.local_running = False
        self.tunnel.ready = True
        self.tunnel.state = "online"

        target, caption = self.dialog._qr_target()

        self.assertEqual(target, "")
        self.assertIn("Сначала включите", caption)

    def test_error_process_does_not_claim_automatic_verification(self) -> None:
        self.tunnel.running = True
        self.tunnel.requested = True
        self.tunnel.ready = False
        self.tunnel.state = "error"

        _target, caption = self.dialog._qr_target()

        self.assertIn("временно недоступен", caption)
        self.assertNotIn("проверяется автоматически", caption)

    def test_disabled_public_tunnel_keeps_explicit_lan_qr(self) -> None:
        self.tunnel.running = False
        self.tunnel.requested = False
        self.tunnel.ready = False
        self.tunnel.state = "off"

        target, caption = self.dialog._qr_target()

        self.assertTrue(target.startswith("http://192.168.1.10:8765/"))
        self.assertIn("#code=123456", target)
        self.assertIn("Wi-Fi-сети", caption)

    def test_disabling_local_server_cancels_pending_public_start(self) -> None:
        self.tunnel.running = False
        self.tunnel.requested = True
        self.tunnel.state = "provisioning"

        self.dialog._on_toggle()

        self.assertEqual(self.tunnel.stop_calls, 1)
        self.assertFalse(self.tunnel.requested)

    def test_close_schedules_parented_dialog_for_deletion(self) -> None:
        parent = QWidget()
        dialog = RemoteAccessDialog(
            is_running=lambda: True,
            start=lambda: None,
            stop=lambda: None,
            lan_url="http://192.168.1.10:8765",
            pair_code="123456",
            tunnel=_FakeTunnel(),
            parent=parent,
        )
        dialog.show()
        dialog.close()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

        self.assertEqual(parent.findChildren(RemoteAccessDialog), [])
        parent.close()


if __name__ == "__main__":
    unittest.main()
