from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from http.client import IncompleteRead
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "NEYROLOCK_5"
sys.path.insert(0, str(APP_ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from core import tunnel as tunnel_module
except (ImportError, ModuleNotFoundError):
    TUNNEL_AVAILABLE = False
else:
    TUNNEL_AVAILABLE = True


class _Config:
    def __init__(self) -> None:
        self.data = {
            "tunnel": {
                "server": "tunnel.invalid",
                "port": 7000,
                "token": "token",
                "secret": "secret",
                "subdomain": "device",
                "domain": "example.invalid",
            }
        }
        self.save_calls = 0

    def save(self) -> bool:
        self.save_calls += 1
        return True


class _Process:
    def __init__(self, stdout=None) -> None:
        self.stdout = stdout
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self) -> None:
        self.returncode = 0

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def kill(self) -> None:
        self.returncode = -9


class _Response:
    def __init__(self, *, status=200, headers=None, body=b"") -> None:
        self.status = status
        self.headers = headers or {}
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


@unittest.skipUnless(TUNNEL_AVAILABLE, "PySide6 is required for tunnel tests")
class TunnelStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tunnel = tunnel_module.Tunnel(_Config(), 8765)

    def _attach(self, process: _Process) -> int:
        with self.tunnel._lock:
            self.tunnel._proc = process
            self.tunnel._enabled_requested = True
            self.tunnel._process_generation += 1
            return self.tunnel._process_generation

    def test_broker_and_legacy_tenant_use_aeza_https_port(self) -> None:
        self.assertEqual(tunnel_module.PUBLIC_HTTPS_PORT, 7443)
        self.assertEqual(
            tunnel_module.BROKER_URL,
            "https://neyroloc.static-assets-io.website:7443",
        )
        self.assertTrue(self.tunnel.configured)
        self.assertNotIn("https_port", self.tunnel.settings)
        self.assertEqual(
            self.tunnel.public_url,
            "https://device.example.invalid:7443",
        )

    def test_standard_https_port_is_omitted_from_public_url(self) -> None:
        self.tunnel._config.data["tunnel"]["https_port"] = 443
        self.assertEqual(
            self.tunnel.public_url,
            "https://device.example.invalid",
        )

    def test_provision_validates_and_persists_public_https_port(self) -> None:
        self.tunnel._config.data["tunnel"] = {}
        response = _Response(
            body=json.dumps({
                "subdomain": "new-device",
                "secret": "tenant-secret",
                "domain": "example.invalid",
                "server": "tunnel.example.invalid",
                "port": 7000,
                "frps_token": "frps-token",
                "https_port": 7443,
            }).encode("utf-8"),
        )
        with mock.patch.object(
            tunnel_module.urllib.request,
            "urlopen",
            return_value=response,
        ):
            self.assertTrue(self.tunnel.provision())

        self.assertEqual(self.tunnel.settings["https_port"], 7443)
        self.assertEqual(
            self.tunnel.public_url,
            "https://new-device.example.invalid:7443",
        )

    def test_provision_rejects_invalid_public_https_port(self) -> None:
        self.tunnel._config.data["tunnel"] = {}
        response = _Response(
            body=json.dumps({
                "subdomain": "new-device",
                "secret": "tenant-secret",
                "domain": "example.invalid",
                "server": "tunnel.example.invalid",
                "port": 7000,
                "frps_token": "frps-token",
                "https_port": 70_000,
            }).encode("utf-8"),
        )
        with mock.patch.object(
            tunnel_module.urllib.request,
            "urlopen",
            return_value=response,
        ):
            self.assertFalse(self.tunnel.provision())

        self.assertEqual(self.tunnel.settings, {})
        self.assertIn("некорректные", self.tunnel.last_status)

    def test_process_start_is_not_public_readiness(self) -> None:
        process = _Process()
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(
                self.tunnel,
                "find_binary",
                return_value=Path(temporary) / "frpc",
            ),
            mock.patch.object(
                self.tunnel,
                "_write_config",
                return_value=Path(temporary) / "frpc.toml",
            ),
            mock.patch.object(tunnel_module.subprocess, "Popen", return_value=process),
            mock.patch.object(tunnel_module.threading, "Thread") as thread,
        ):
            self.assertTrue(self.tunnel.start())

        self.assertEqual(thread.return_value.start.call_count, 2)
        self.assertTrue(self.tunnel.running)
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.STARTING)
        self.assertFalse(self.tunnel.ready)

    def test_success_marker_requires_public_https_verification(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._handle_output_line(
            "connect to server error: timeout",
            process,
            process_generation,
        )
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.RETRYING)
        self.assertFalse(self.tunnel.ready)

        with mock.patch.object(self.tunnel, "_start_public_verification") as verify:
            self.tunnel._handle_output_line(
                "start proxy success",
                process,
                process_generation,
            )
        args = verify.call_args.args
        self.assertIs(args[0], process)
        self.assertEqual(args[1], process_generation)
        self.assertEqual(args[2], self.tunnel._connection_generation)
        self.assertIs(args[3], self.tunnel._verify_cancel)
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.STARTING)
        self.assertFalse(self.tunnel.ready)

    def test_verified_public_https_makes_address_ready(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._connection_generation = 3
        cancel = self.tunnel._verify_cancel
        with mock.patch.object(
            self.tunnel,
            "_public_url_reaches_remote_server",
            return_value=True,
        ), mock.patch.object(cancel, "wait", return_value=True):
            self.tunnel._verify_public_url(
                process,
                process_generation,
                3,
                cancel,
            )
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.ONLINE)
        self.assertTrue(self.tunnel.ready)

    def test_repeated_failed_health_checks_recycle_frpc_once(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._connection_generation = 5
        cancel = self.tunnel._verify_cancel
        with (
            mock.patch.object(
                self.tunnel,
                "_public_url_reaches_remote_server",
                return_value=False,
            ),
            mock.patch.object(cancel, "wait", return_value=False),
            mock.patch.object(
                self.tunnel,
                "_request_process_recycle",
                return_value=True,
            ) as recycle,
        ):
            self.tunnel._verify_public_url(
                process,
                process_generation,
                5,
                cancel,
            )

        recycle.assert_called_once_with(process, process_generation, 5, cancel)

    def test_periodic_probe_revokes_online_when_https_later_fails(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._connection_generation = 7
        cancel = self.tunnel._verify_cancel
        with mock.patch.object(
            self.tunnel,
            "_public_url_reaches_remote_server",
            side_effect=[True, False, False],
        ), mock.patch.object(cancel, "wait", side_effect=[False, False, True]):
            self.tunnel._verify_public_url(
                process,
                process_generation,
                7,
                cancel,
            )
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.RETRYING)
        self.assertFalse(self.tunnel.ready)

    def test_single_periodic_probe_failure_keeps_verified_url_ready(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._connection_generation = 8
        cancel = self.tunnel._verify_cancel
        with mock.patch.object(
            self.tunnel,
            "_public_url_reaches_remote_server",
            side_effect=[True, False],
        ), mock.patch.object(cancel, "wait", side_effect=[False, True]):
            self.tunnel._verify_public_url(
                process,
                process_generation,
                8,
                cancel,
            )

        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.ONLINE)
        self.assertTrue(self.tunnel.ready)

    def test_public_probe_requires_exact_remote_server_fingerprint(self) -> None:
        exact = _Response(
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-NEYROLOC-Remote": "health-v1",
            },
            body=b'{"ok":true,"service":"neyroloc-remote","version":1}',
        )
        with mock.patch.object(
            tunnel_module.urllib.request,
            "urlopen",
            return_value=exact,
        ) as urlopen:
            self.assertTrue(self.tunnel._public_url_reaches_remote_server())
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://device.example.invalid:7443/api/healthz",
        )
        self.assertEqual(
            urlopen.call_args.kwargs["timeout"],
            tunnel_module.PUBLIC_CHECK_TIMEOUT_SECONDS,
        )
        self.assertGreaterEqual(tunnel_module.PUBLIC_CHECK_TIMEOUT_SECONDS, 12)

        wrong_landing = _Response(
            headers={"Content-Type": "text/html"},
            body=b"<html>landing</html>",
        )
        with mock.patch.object(
            tunnel_module.urllib.request,
            "urlopen",
            return_value=wrong_landing,
        ):
            self.assertFalse(self.tunnel._public_url_reaches_remote_server())

        compatible = _Response(
            headers={
                "Content-Type": "application/json",
                "X-NEYROLOC-Remote": "health-v1",
            },
            body=(
                b'{"ok":true,"service":"neyroloc-remote","version":1,'
                b'"build":"new"}'
            ),
        )
        with mock.patch.object(
            tunnel_module.urllib.request,
            "urlopen",
            return_value=compatible,
        ):
            self.assertTrue(self.tunnel._public_url_reaches_remote_server())

    def test_incomplete_public_response_becomes_retrying_not_dead_verifier(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._connection_generation = 9
        cancel = self.tunnel._verify_cancel
        broken = _Response(
            headers={
                "Content-Type": "application/json",
                "X-NEYROLOC-Remote": "health-v1",
            },
        )

        def incomplete(_limit: int) -> bytes:
            raise IncompleteRead(b"", 1)

        broken.read = incomplete
        with (
            mock.patch.object(
                tunnel_module.urllib.request,
                "urlopen",
                return_value=broken,
            ),
            mock.patch.object(cancel, "wait", return_value=True),
        ):
            self.tunnel._verify_public_url(
                process,
                process_generation,
                9,
                cancel,
            )

        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.RETRYING)
        self.assertFalse(self.tunnel.ready)

    def test_malformed_public_url_is_a_failed_probe(self) -> None:
        with mock.patch.object(
            tunnel_module.urllib.request,
            "Request",
            side_effect=ValueError("bad URL"),
        ):
            self.assertFalse(self.tunnel._public_url_reaches_remote_server())

    def test_legacy_production_config_migrates_control_channel_to_wss(self) -> None:
        self.tunnel._config.data["tunnel"].update(
            {
                "server": tunnel_module.PUBLIC_BASE_DOMAIN,
                "domain": tunnel_module.PUBLIC_BASE_DOMAIN,
                "port": 7000,
                "https_port": 7443,
            }
        )
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            tunnel_module,
            "FRPC_CONFIG",
            Path(temporary) / "frpc.toml",
        ):
            text = self.tunnel._write_config().read_text(encoding="utf-8")

        self.assertIn("serverPort = 7443", text)
        self.assertIn('transport.protocol = "wss"', text)
        self.assertIn("transport.tcpMuxKeepaliveInterval = 10", text)
        self.assertEqual(self.tunnel.settings["protocol"], "wss")
        self.assertEqual(self.tunnel.settings["port"], 7443)
        self.assertEqual(self.tunnel.settings["https_port"], 7443)
        self.assertEqual(self.tunnel._config.save_calls, 1)

    def test_public_preference_is_persisted_until_explicit_stop(self) -> None:
        self.assertFalse(self.tunnel.auto_start_enabled)
        with mock.patch.object(tunnel_module.threading, "Thread"):
            self.assertTrue(self.tunnel.start_async())
        self.assertTrue(self.tunnel.auto_start_enabled)

        self.tunnel.stop(wait=True)
        self.assertFalse(self.tunnel.auto_start_enabled)

    def test_unexpected_process_exit_preserves_intent_and_schedules_restart(self) -> None:
        # A real frpc writes a final shutdown line after poll() already exposes
        # the exit code; the reader must still reach its cleanup path.
        process = _Process(stdout=["process exited\n"])
        process.returncode = 1
        process_generation = self._attach(process)
        with mock.patch.object(tunnel_module.threading, "Thread") as thread:
            self.tunnel._read_output(process, process_generation)

        self.assertTrue(self.tunnel.requested)
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.RETRYING)
        thread.return_value.start.assert_called_once()

    def test_explicit_stop_cancels_scheduled_restart(self) -> None:
        with self.tunnel._lock:
            self.tunnel._enabled_requested = True
            start_generation = self.tunnel._start_generation
            cancel = self.tunnel._restart_cancel
        self.tunnel.stop(wait=True)
        with mock.patch.object(self.tunnel, "start_async") as start:
            self.tunnel._restart_after_delay(start_generation, cancel, 0)
        start.assert_not_called()

    def test_auth_failure_is_safe_and_distinct_from_network_retry(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        sensitive_detail = "bad secret: must-not-be-shown"
        self.tunnel._handle_output_line(
            f"login to server failed: {sensitive_detail}",
            process,
            process_generation,
        )
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.ERROR)
        self.assertNotIn(sensitive_detail, self.tunnel.last_status)
        self.assertIn("отклонил", self.tunnel.last_status)

    def test_invalid_runtime_config_is_reported_without_crashing(self) -> None:
        self.tunnel._config.data["tunnel"]["port"] = "invalid"
        with mock.patch.object(
            self.tunnel,
            "find_binary",
            return_value=Path("/tmp/frpc"),
        ):
            self.assertFalse(self.tunnel.start())
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.ERROR)
        self.assertIn("Некорректный порт", self.tunnel.last_status)

    def test_stop_during_probe_cannot_restore_retrying_state(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        self.tunnel._connection_generation = 4
        cancel = self.tunnel._verify_cancel

        def stop_then_fail() -> bool:
            self.tunnel.stop(wait=True)
            return False

        with mock.patch.object(
            self.tunnel,
            "_public_url_reaches_remote_server",
            side_effect=stop_then_fail,
        ):
            self.tunnel._verify_public_url(
                process,
                process_generation,
                4,
                cancel,
            )

        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.OFF)

    def test_old_reader_cannot_change_replacement_process(self) -> None:
        old_process = _Process(stdout=[])
        old_generation = self._attach(old_process)
        new_process = _Process()
        new_generation = self._attach(new_process)
        self.tunnel._set_state(tunnel_module.TunnelState.STARTING, "new process")
        running_events: list[bool] = []
        self.tunnel.runningChanged.connect(running_events.append)

        self.tunnel._read_output(old_process, old_generation)
        self.tunnel._handle_output_line(
            "connect to server error: stale",
            old_process,
            old_generation,
        )

        self.assertIs(self.tunnel._proc, new_process)
        self.assertEqual(self.tunnel._process_generation, new_generation)
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.STARTING)
        self.assertEqual(running_events, [])

    def test_close_waits_for_an_existing_async_stopper(self) -> None:
        stopper = mock.Mock()
        with self.tunnel._lock:
            self.tunnel._proc = None
            self.tunnel._terminating = True
            self.tunnel._stopper = stopper

        self.tunnel.stop(wait=True)

        stopper.join.assert_called_once_with(timeout=5)
        self.assertTrue(self.tunnel._terminating)

    def test_stop_cannot_emit_off_before_an_older_online_event(self) -> None:
        process = _Process()
        process_generation = self._attach(process)
        entered_emit = threading.Event()
        release_emit = threading.Event()
        state_events: list[str] = []
        original_emit = self.tunnel._emit_state_changes

        def blocking_emit(state, status, state_changed, status_changed) -> None:
            if state is tunnel_module.TunnelState.ONLINE:
                entered_emit.set()
                release_emit.wait(timeout=2)
            if state_changed:
                state_events.append(state.value)
            original_emit(state, status, state_changed, status_changed)

        with mock.patch.object(
            self.tunnel,
            "_emit_state_changes",
            side_effect=blocking_emit,
        ):
            online = threading.Thread(
                target=self.tunnel._set_state_if_current,
                args=(
                    process,
                    process_generation,
                    tunnel_module.TunnelState.ONLINE,
                    "online",
                ),
            )
            online.start()
            self.assertTrue(entered_emit.wait(timeout=1))
            stopping = threading.Thread(
                target=self.tunnel.stop,
                kwargs={"wait": True},
            )
            stopping.start()
            self.assertTrue(stopping.is_alive())
            release_emit.set()
            online.join(timeout=2)
            stopping.join(timeout=2)

        self.assertEqual(state_events[-3:], ["online", "stopping", "off"])
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.OFF)

    def test_async_stop_stays_stopping_until_process_has_exited(self) -> None:
        release = threading.Event()

        class BlockingProcess(_Process):
            def __init__(self) -> None:
                super().__init__()
                self.terminate_called = False

            def terminate(self) -> None:
                self.terminate_called = True

            def wait(self, timeout=None):
                if not release.wait(timeout=timeout):
                    raise tunnel_module.subprocess.TimeoutExpired("frpc", timeout)
                self.returncode = 0
                return 0

        process = BlockingProcess()
        self._attach(process)

        self.tunnel.stop()

        self.assertTrue(process.terminate_called)
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.STOPPING)
        self.assertIs(self.tunnel._proc, process)
        self.assertFalse(self.tunnel.ready)

        release.set()
        stopper = self.tunnel._stopper
        self.assertIsNotNone(stopper)
        stopper.join(timeout=2)
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.OFF)
        self.assertIsNone(self.tunnel._proc)

    def test_failed_process_termination_never_claims_off(self) -> None:
        class UnkillableProcess(_Process):
            def terminate(self) -> None:
                pass

            def wait(self, timeout=None):
                raise tunnel_module.subprocess.TimeoutExpired("frpc", timeout)

            def kill(self) -> None:
                pass

        process = UnkillableProcess()
        self._attach(process)

        self.tunnel.stop(wait=True)

        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.ERROR)
        self.assertIs(self.tunnel._proc, process)
        self.assertTrue(self.tunnel.running)
        self.assertTrue(self.tunnel.requested)
        self.assertNotEqual(
            self.tunnel.last_status,
            "Публичный доступ выключен.",
        )

    def test_late_frpc_success_cannot_escape_stopping(self) -> None:
        release = threading.Event()

        class BlockingProcess(_Process):
            def terminate(self) -> None:
                pass

            def wait(self, timeout=None):
                if not release.wait(timeout=timeout):
                    raise tunnel_module.subprocess.TimeoutExpired("frpc", timeout)
                self.returncode = 0
                return 0

        process = BlockingProcess()
        process_generation = self._attach(process)
        self.tunnel.stop()

        with mock.patch.object(self.tunnel, "_start_public_verification") as verify:
            self.tunnel._handle_output_line(
                "start proxy success",
                process,
                process_generation,
            )

        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.STOPPING)
        self.assertFalse(self.tunnel.ready)
        verify.assert_not_called()
        release.set()
        stopper = self.tunnel._stopper
        self.assertIsNotNone(stopper)
        stopper.join(timeout=2)

    def test_cancel_during_async_provision_never_spawns_frpc(self) -> None:
        self.tunnel._config.data["tunnel"] = {}
        entered = threading.Event()
        release = threading.Event()

        def blocked_provision(*_args, **_kwargs) -> bool:
            entered.set()
            release.wait(timeout=2)
            return True

        with (
            mock.patch.object(
                self.tunnel,
                "provision",
                side_effect=blocked_provision,
            ),
            mock.patch.object(tunnel_module.subprocess, "Popen") as popen,
        ):
            self.assertTrue(self.tunnel.start_async())
            self.assertTrue(entered.wait(timeout=1))
            self.assertEqual(
                self.tunnel.state,
                tunnel_module.TunnelState.PROVISIONING,
            )
            self.tunnel.stop(wait=True)
            release.set()
            worker = self.tunnel._start_worker
            if worker is not None:
                worker.join(timeout=2)

        popen.assert_not_called()
        self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.OFF)
        self.assertFalse(self.tunnel.requested)

    def test_unexpected_async_start_error_cleans_worker_for_retry(self) -> None:
        entered = threading.Event()
        release = threading.Event()
        calls = 0

        def start(*_args, **_kwargs) -> bool:
            nonlocal calls
            calls += 1
            if calls == 1:
                entered.set()
                release.wait(timeout=2)
                raise TypeError("malformed setting")
            return False

        with mock.patch.object(
            self.tunnel,
            "start",
            side_effect=start,
        ):
            self.assertTrue(self.tunnel.start_async())
            self.assertTrue(entered.wait(timeout=1))
            first_worker = self.tunnel._start_worker
            self.assertIsNotNone(first_worker)
            release.set()
            first_worker.join(timeout=2)

            self.assertEqual(self.tunnel.state, tunnel_module.TunnelState.ERROR)
            self.assertIsNone(self.tunnel._start_worker)
            self.assertFalse(self.tunnel.requested)
            self.assertNotIn("malformed setting", self.tunnel.last_status)

            self.assertTrue(self.tunnel.start_async())
            second_worker = self.tunnel._start_worker
            if second_worker is not None:
                self.assertIsNot(second_worker, first_worker)
                second_worker.join(timeout=2)

        self.assertEqual(calls, 2)
        self.assertIsNone(self.tunnel._start_worker)

    def test_malformed_custom_binary_setting_never_raises(self) -> None:
        self.tunnel._config.data["tunnel"]["frpc_path"] = 123
        with mock.patch.object(tunnel_module.shutil, "which", return_value=None):
            result = self.tunnel.find_binary()
        self.assertTrue(result is None or isinstance(result, Path))

    def test_immediate_reenable_after_cancel_restarts_when_worker_exits(self) -> None:
        self.tunnel._config.data["tunnel"] = {}
        entered = threading.Event()
        release = threading.Event()
        spawned = threading.Event()
        process = _Process()
        configured_values = _Config().data["tunnel"]
        provision_calls = 0

        def provision(*_args, **_kwargs) -> bool:
            nonlocal provision_calls
            provision_calls += 1
            if provision_calls == 1:
                entered.set()
                release.wait(timeout=2)
                return False
            self.tunnel._config.data["tunnel"] = dict(configured_values)
            return True

        def spawn(*_args, **_kwargs):
            spawned.set()
            return process

        with (
            mock.patch.object(self.tunnel, "provision", side_effect=provision),
            mock.patch.object(
                self.tunnel,
                "find_binary",
                return_value=Path("/tmp/frpc"),
            ),
            mock.patch.object(
                self.tunnel,
                "_write_config",
                return_value=Path("/tmp/frpc.toml"),
            ),
            mock.patch.object(
                tunnel_module.subprocess,
                "Popen",
                side_effect=spawn,
            ),
        ):
            self.assertTrue(self.tunnel.start_async())
            self.assertTrue(entered.wait(timeout=1))
            self.tunnel.stop(wait=True)
            self.assertTrue(self.tunnel.start_async())
            self.assertTrue(self.tunnel.requested)
            release.set()
            self.assertTrue(spawned.wait(timeout=2))

        self.assertEqual(provision_calls, 2)
        self.assertTrue(self.tunnel.running)
        self.tunnel.stop(wait=True)


if __name__ == "__main__":
    unittest.main()
